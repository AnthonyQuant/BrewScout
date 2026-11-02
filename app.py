import os
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse, urljoin
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import OperationalError

from config import Config, INSTANCE_DIR
from models import db, Cafe, VerificationReport, User, Review, ReviewReply, ReviewVote
from forms import AddCafeForm, VerificationReportForm, UserRegisterForm, UserLoginForm, AdminLoginForm, ReviewForm, ReplyForm

csrf = CSRFProtect()


def is_safe_url(target: str) -> bool:
    """Validates that a redirect target is a safe local URL."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def create_app(config_class=Config):
    app = Flask(__name__, instance_path=str(INSTANCE_DIR))
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    csrf.init_app(app)  # Registers csrf_token() in Jinja template globals

    with app.app_context():
        try:
            db.create_all()
        except OperationalError as exc:
            raise RuntimeError(f"Could not open database at {db.engine.url.database!r}.") from exc

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in or create an account to perform this action.", "warning")
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('is_admin'):
                flash("Admin authorization required to access the management portal.", "danger")
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/')
    def index():
        search_query = request.args.get('q', '').strip()
        zip_filter = request.args.get('zip_code', '').strip()
        min_wifi = request.args.get('min_wifi', type=int, default=0)
        min_outlets = request.args.get('min_outlets', type=float, default=0.0)
        price_tier = request.args.get('price_range', '').strip()
        quiet_only = request.args.get('quiet_only', type=int, default=0)
        backup_power_only = request.args.get('has_backup_power', type=int, default=0)
        meeting_friendly_only = request.args.get('is_meeting_friendly', type=int, default=0)
        sort_by = request.args.get('sort_by', 'workability', type=str)

        query = db.session.query(Cafe).filter(Cafe.is_approved == True)

        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter(
                (Cafe.name.ilike(pattern)) |
                (Cafe.location.ilike(pattern)) |
                (Cafe.address.ilike(pattern)) |
                (Cafe.zip_code.ilike(pattern))
            )

        if zip_filter:
            query = query.filter(Cafe.zip_code.ilike(f"%{zip_filter}%"))

        if min_wifi > 0:
            query = query.filter(Cafe.wifi_speed_mbps >= min_wifi)

        if min_outlets > 0:
            query = query.filter(Cafe.power_outlet_score >= min_outlets)

        if price_tier:
            query = query.filter(Cafe.price_range == price_tier)

        if quiet_only == 1:
            query = query.filter(Cafe.noise_level_score >= 7.5)

        if backup_power_only == 1:
            query = query.filter(Cafe.has_backup_power == True)

        if meeting_friendly_only == 1:
            query = query.filter(Cafe.is_meeting_friendly == True)

        cafes = query.all()

        for cafe in cafes:
            cafe.calculated_workability = min(10.0, max(0.0, cafe.calculate_workability_score()))

        if sort_by == 'wifi_speed':
            cafes = sorted(cafes, key=lambda c: c.wifi_speed_mbps, reverse=True)
        elif sort_by == 'outlets':
            cafes = sorted(cafes, key=lambda c: c.power_outlet_score, reverse=True)
        elif sort_by == 'affordability':
            cafes = sorted(cafes, key=lambda c: c.affordability_score, reverse=True)
        elif sort_by == 'newest':
            cafes = sorted(cafes, key=lambda c: c.created_at, reverse=True)
        else:
            cafes = sorted(cafes, key=lambda c: c.calculated_workability, reverse=True)

        return render_template('index.html', cafes=cafes)

    @app.route('/analytics')
    def analytics():
        approved_cafes = db.session.query(Cafe).filter(Cafe.is_approved == True).all()
        total_cafes = len(approved_cafes)

        if total_cafes == 0:
            return render_template('analytics.html', total_cafes=0)

        avg_wifi_speed = round(sum(c.wifi_speed_mbps for c in approved_cafes) / total_cafes, 1)
        backup_power_pct = round((sum(1 for c in approved_cafes if c.has_backup_power) / total_cafes) * 100)
        meeting_friendly_pct = round((sum(1 for c in approved_cafes if c.is_meeting_friendly) / total_cafes) * 100)

        for c in approved_cafes:
            c.calculated_workability = min(10.0, max(0.0, c.calculate_workability_score()))

        top_workability = sorted(approved_cafes, key=lambda c: c.calculated_workability, reverse=True)[:5]
        fastest_wifi = sorted(approved_cafes, key=lambda c: c.wifi_speed_mbps, reverse=True)[:5]
        best_outlets = sorted(approved_cafes, key=lambda c: c.power_outlet_score, reverse=True)[:5]

        price_counts = {
            'Budget-friendly': sum(1 for c in approved_cafes if c.price_range == 'Budget-friendly'),
            'Moderate': sum(1 for c in approved_cafes if c.price_range == 'Moderate'),
            'Flexible': sum(1 for c in approved_cafes if c.price_range == 'Flexible')
        }

        return render_template(
            'analytics.html',
            total_cafes=total_cafes,
            avg_wifi_speed=avg_wifi_speed,
            backup_power_pct=backup_power_pct,
            meeting_friendly_pct=meeting_friendly_pct,
            top_workability=top_workability,
            fastest_wifi=fastest_wifi,
            best_outlets=best_outlets,
            price_counts=price_counts
        )

    @app.route('/compare')
    def compare_cafes():
        all_cafes = db.session.query(Cafe).filter(Cafe.is_approved == True).order_by(Cafe.name.asc()).all()

        selected_ids = []
        for param in ['cafe1', 'cafe2', 'cafe3', 'cafe4']:
            cid = request.args.get(param, type=int)
            if cid and cid not in selected_ids:
                selected_ids.append(cid)

        selected_cafes = []
        if selected_ids:
            fetched_cafes = db.session.query(Cafe).filter(
                Cafe.id.in_(selected_ids),
                Cafe.is_approved == True
            ).all()
            cafes_dict = {c.id: c for c in fetched_cafes}
            selected_cafes = [cafes_dict[cid] for cid in selected_ids if cid in cafes_dict]

            for c in selected_cafes:
                c.calculated_workability = min(10.0, max(0.0, c.calculate_workability_score()))

        return render_template('compare.html', all_cafes=all_cafes, selected_cafes=selected_cafes, selected_ids=selected_ids)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('index'))
        form = UserRegisterForm()
        if form.validate_on_submit():
            existing_user = db.session.query(User).filter(User.email.ilike(form.email.data.strip())).first()
            if existing_user:
                flash("An account with this email address already exists. Please log in.", "warning")
                return redirect(url_for('login'))

            new_user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower()
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()

            session.clear()
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name
            flash(f"Welcome to BrewScout, {new_user.name}! Your account was created successfully.", "success")
            return redirect(url_for('add_cafe'))

        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('index'))
        form = UserLoginForm()
        if form.validate_on_submit():
            user = db.session.query(User).filter(User.email.ilike(form.email.data.strip())).first()
            if user and user.check_password(form.password.data):
                session.clear()
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash(f"Welcome back, {user.name}!", "success")

                next_page = request.args.get('next')
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for('index'))

            flash("Invalid email or password. Please try again.", "danger")

        return render_template('login.html', form=form)

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for('index'))

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        form = AdminLoginForm()
        if form.validate_on_submit():
            if (form.email.data.strip().lower() == app.config['ADMIN_EMAIL'].lower() and
                form.password.data == app.config['ADMIN_PASSWORD']):
                session['is_admin'] = True
                flash("Admin authentication successful.", "success")
                return redirect(url_for('admin_dashboard'))
            flash("Invalid admin credentials.", "danger")

        return render_template('admin_login.html', form=form)

    @app.route('/admin/logout', methods=['POST'])
    def admin_logout():
        session.pop('is_admin', None)
        flash("Admin session closed.", "info")
        return redirect(url_for('index'))

    @app.route('/cafe/<int:cafe_id>', methods=['GET', 'POST'])
    def cafe_detail(cafe_id):
        cafe = db.session.query(Cafe).filter(Cafe.id == cafe_id, Cafe.is_approved == True).first_or_404()
        cafe.calculated_workability = min(10.0, max(0.0, cafe.calculate_workability_score()))

        verify_form = VerificationReportForm()
        review_form = ReviewForm()
        reply_form = ReplyForm()

        if request.method == 'POST':
            if 'submit_verification' in request.form and verify_form.validate_on_submit():
                report = VerificationReport(
                    cafe_id=cafe.id,
                    reporter_name=verify_form.reporter_name.data.strip() if verify_form.reporter_name.data else 'Anonymous Contributor',
                    wifi_speed_mbps=verify_form.wifi_speed_mbps.data,
                    price_range=verify_form.price_range.data if verify_form.price_range.data else None,
                    opening_hours=verify_form.opening_hours.data.strip() if verify_form.opening_hours.data else None,
                    notes=verify_form.notes.data.strip()
                )
                cafe.verification_status = 'Community Reported'
                db.session.add(report)
                db.session.commit()
                flash("Re-verification report submitted! An admin will review your update.", "success")
                return redirect(url_for('cafe_detail', cafe_id=cafe.id))

            if 'submit_review' in request.form:
                if 'user_id' not in session:
                    flash("Please log in or register to post a review.", "warning")
                    return redirect(url_for('login', next=request.url))

                if review_form.validate_on_submit():
                    new_review = Review(
                        cafe_id=cafe.id,
                        user_id=session.get('user_id'),
                        author_name=session.get('user_name', 'Anonymous Coder'),
                        rating=review_form.rating.data,
                        comment=review_form.comment.data.strip(),
                        is_approved=False
                    )
                    db.session.add(new_review)
                    db.session.commit()
                    flash("Thank you! Your review has been submitted and is pending admin approval.", "info")
                    return redirect(url_for('cafe_detail', cafe_id=cafe.id))

            if 'submit_reply' in request.form:
                if 'user_id' not in session:
                    flash("Please log in or register to reply to reviews.", "warning")
                    return redirect(url_for('login', next=request.url))

                target_review_id = request.form.get('target_review_id', type=int)
                if target_review_id and reply_form.validate_on_submit():
                    new_reply = ReviewReply(
                        review_id=target_review_id,
                        user_id=session.get('user_id'),
                        author_name=session.get('user_name', 'Anonymous Contributor'),
                        comment=reply_form.comment.data.strip(),
                        is_approved=False
                    )
                    db.session.add(new_reply)
                    db.session.commit()
                    flash("Your reply has been submitted and is pending admin approval.", "info")
                    return redirect(url_for('cafe_detail', cafe_id=cafe.id))

        approved_reviews = db.session.query(Review).filter(
            Review.cafe_id == cafe.id,
            Review.is_approved == True
        ).order_by(Review.created_at.desc()).all()

        user_pending_reviews = []
        if session.get('user_id'):
            user_pending_reviews = db.session.query(Review).filter(
                Review.cafe_id == cafe.id,
                Review.user_id == session.get('user_id'),
                Review.is_approved == False
            ).order_by(Review.created_at.desc()).all()

        reviews = user_pending_reviews + approved_reviews

        return render_template(
            'cafe_detail.html',
            cafe=cafe,
            verify_form=verify_form,
            review_form=review_form,
            reply_form=reply_form,
            reviews=reviews
        )

    @app.route('/review/<int:review_id>/vote/<string:vote_type>', methods=['POST'])
    @login_required
    def vote_review(review_id, vote_type):
        if vote_type not in ['like', 'dislike']:
            flash("Invalid vote type.", "warning")
            return redirect(request.referrer or url_for('index'))

        review = db.session.query(Review).get_or_404(review_id)
        if not review.is_approved:
            flash("Votes can only be cast on approved reviews.", "warning")
            return redirect(request.referrer or url_for('index'))

        existing_vote = db.session.query(ReviewVote).filter(
            ReviewVote.review_id == review_id,
            ReviewVote.user_id == session['user_id']
        ).first()

        if existing_vote:
            if existing_vote.vote_type == vote_type:
                db.session.delete(existing_vote)
                flash("Your vote was removed.", "info")
            else:
                existing_vote.vote_type = vote_type
                flash(f"Vote updated to {vote_type}.", "success")
        else:
            new_vote = ReviewVote(
                review_id=review_id,
                user_id=session['user_id'],
                vote_type=vote_type
            )
            db.session.add(new_vote)
            flash(f"Thank you! Your {vote_type} was recorded.", "success")

        db.session.commit()
        return redirect(request.referrer or url_for('cafe_detail', cafe_id=review.cafe_id))

    @app.route('/plan-session')
    def plan_session():
        activity = request.args.get('activity', 'coding')
        duration = request.args.get('duration', '3', type=str)
        spending = request.args.get('spending', 'Moderate')
        priority = request.args.get('priority', 'wifi_power')

        weights = {
            'wifi': 0.20,
            'outlets': 0.20,
            'noise': 0.20,
            'seating': 0.15,
            'affordability': 0.15,
            'hours': 0.10
        }

        if activity == 'coding':
            weights['wifi'], weights['outlets'] = 0.30, 0.25
        elif activity == 'studying':
            weights['noise'], weights['seating'] = 0.30, 0.25
        elif activity == 'team':
            weights['seating'], weights['wifi'], weights['noise'] = 0.25, 0.20, 0.20
        elif activity == 'casual':
            weights['affordability'], weights['seating'] = 0.25, 0.20

        try:
            duration_hours = float(duration)
        except ValueError:
            duration_hours = 3.0

        if duration_hours >= 4.0:
            weights['seating'] += 0.10
            weights['outlets'] += 0.10
            weights['hours'] += 0.05
        elif duration_hours <= 1.5:
            weights['wifi'] += 0.05

        if spending.lower() in ['budget-friendly', 'budget', 'low']:
            weights['affordability'] += 0.15
        elif spending.lower() == 'moderate':
            weights['affordability'] += 0.05

        if priority == 'wifi_power':
            weights['wifi'] += 0.10
            weights['outlets'] += 0.10
        elif priority == 'quiet':
            weights['noise'] += 0.15

        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        cafes = db.session.query(Cafe).filter(Cafe.is_approved == True).all()
        for cafe in cafes:
            raw_score = cafe.calculate_workability_score(custom_weights=weights)
            cafe.tailored_score = min(10.0, max(0.0, raw_score))

            reasons = []
            if cafe.wifi_quality_score >= 8.5:
                reasons.append("Ultra-fast Wi-Fi")
            if cafe.power_outlet_score >= 8.5:
                reasons.append("accessible power outlets")
            if cafe.noise_level_score >= 8.0:
                reasons.append("quiet working environment")
            if cafe.has_backup_power:
                reasons.append("generator/backup power on-site")
            cafe.match_reason = ", ".join(reasons) if reasons else "Balanced workspace amenities."

        recommendations = sorted(cafes, key=lambda c: c.tailored_score, reverse=True)

        no_good_match = False
        if recommendations and recommendations[0].tailored_score < 5.0:
            no_good_match = True
            flash("No available cafes met the minimum suitability threshold for your requested criteria.", "warning")

        return render_template(
            'plan_session.html',
            recommendations=recommendations,
            no_good_match=no_good_match
        )

    @app.route('/add', methods=['GET', 'POST'])
    @login_required
    def add_cafe():
        form = AddCafeForm()
        if form.validate_on_submit():
            existing_cafe = db.session.query(Cafe).filter(
                Cafe.name.ilike(form.name.data.strip()),
                Cafe.location.ilike(form.location.data.strip())
            ).first()

            if existing_cafe:
                flash("A cafe with this name and location already exists in our system.", "warning")
                return render_template('add_cafe.html', form=form)

            new_cafe = Cafe(
                name=form.name.data.strip(),
                location=form.location.data.strip(),
                zip_code=form.zip_code.data.strip() if form.zip_code.data else None,
                address=form.address.data.strip(),
                google_maps_url=form.google_maps_url.data.strip() if form.google_maps_url.data else "",
                img_url=form.img_url.data.strip() if form.img_url.data else None,
                opening_hours=form.opening_hours.data.strip(),
                price_range=form.price_range.data,
                seating_capacity=form.seating_capacity.data.strip(),
                has_backup_power=bool(int(form.has_backup_power.data)),
                socket_accessibility=form.socket_accessibility.data,
                is_meeting_friendly=bool(int(form.is_meeting_friendly.data)),
                wifi_speed_mbps=form.wifi_speed_mbps.data,
                wifi_quality_score=form.wifi_quality_score.data,
                power_outlet_score=form.power_outlet_score.data,
                noise_level_score=form.noise_level_score.data,
                seating_comfort_score=form.seating_comfort_score.data,
                affordability_score=form.affordability_score.data,
                opening_hours_score=form.opening_hours_score.data,
                is_approved=False,
                user_id=session.get('user_id'),
                last_verified_date=datetime.utcnow(),
                verification_status='Recently Checked',
                wifi_last_tested_date=datetime.utcnow()
            )
            db.session.add(new_cafe)
            db.session.commit()

            flash("Thank you! Your cafe submission has been received and is pending admin approval.", "info")
            return redirect(url_for('index'))

        return render_template('add_cafe.html', form=form)

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        pending_cafes = db.session.query(Cafe).filter(Cafe.is_approved == False).order_by(Cafe.created_at.desc()).all()
        approved_cafes = db.session.query(Cafe).filter(Cafe.is_approved == True).order_by(Cafe.name.asc()).all()
        pending_reports = db.session.query(VerificationReport).filter(VerificationReport.is_processed == False).order_by(VerificationReport.created_at.desc()).all()
        pending_reviews = db.session.query(Review).filter(Review.is_approved == False).order_by(Review.created_at.desc()).all()
        pending_replies = db.session.query(ReviewReply).filter(ReviewReply.is_approved == False).order_by(ReviewReply.created_at.desc()).all()

        return render_template(
            'admin.html',
            pending_cafes=pending_cafes,
            approved_cafes=approved_cafes,
            pending_reports=pending_reports,
            pending_reviews=pending_reviews,
            pending_replies=pending_replies
        )

    @app.route('/admin/approve-review/<int:review_id>', methods=['POST'])
    @admin_required
    def approve_review(review_id):
        review = db.session.query(Review).get_or_404(review_id)
        review.is_approved = True
        db.session.commit()
        flash("Review approved and published publicly.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete-review/<int:review_id>', methods=['POST'])
    @admin_required
    def delete_review(review_id):
        review = db.session.query(Review).get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        flash("Review deleted.", "info")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/approve-reply/<int:reply_id>', methods=['POST'])
    @admin_required
    def approve_reply(reply_id):
        reply = db.session.query(ReviewReply).get_or_404(reply_id)
        reply.is_approved = True
        db.session.commit()
        flash("Reply approved and published publicly.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete-reply/<int:reply_id>', methods=['POST'])
    @admin_required
    def delete_reply(reply_id):
        reply = db.session.query(ReviewReply).get_or_404(reply_id)
        db.session.delete(reply)
        db.session.commit()
        flash("Reply deleted.", "info")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/approve/<int:cafe_id>', methods=['POST'])
    @admin_required
    def approve_cafe(cafe_id):
        cafe = db.session.query(Cafe).get_or_404(cafe_id)
        cafe.is_approved = True
        cafe.last_verified_date = datetime.utcnow()
        cafe.verification_status = 'Recently Checked'
        db.session.commit()
        flash(f"'{cafe.name}' approved and published.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/revoke/<int:cafe_id>', methods=['POST'])
    @admin_required
    def revoke_approval(cafe_id):
        cafe = db.session.query(Cafe).get_or_404(cafe_id)
        cafe.is_approved = False
        db.session.commit()
        flash(f"Approval ejected! '{cafe.name}' moved back to pending queue.", "warning")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete/<int:cafe_id>', methods=['POST'])
    @admin_required
    def delete_cafe(cafe_id):
        cafe = db.session.query(Cafe).get_or_404(cafe_id)
        cafe_name = cafe.name
        db.session.delete(cafe)
        db.session.commit()
        flash(f"'{cafe_name}' permanently deleted.", "info")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/approve-report/<int:report_id>', methods=['POST'])
    @admin_required
    def approve_report(report_id):
        report = db.session.query(VerificationReport).get_or_404(report_id)
        cafe = report.cafe
        if report.wifi_speed_mbps:
            cafe.wifi_speed_mbps = report.wifi_speed_mbps
            cafe.wifi_last_tested_date = datetime.utcnow()
        if report.price_range:
            cafe.price_range = report.price_range
        if report.opening_hours:
            cafe.opening_hours = report.opening_hours

        cafe.last_verified_date = datetime.utcnow()
        cafe.verification_status = 'Recently Checked'
        report.is_processed = True
        db.session.commit()
        flash(f"Report for '{cafe.name}' approved and metrics updated!", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete-report/<int:report_id>', methods=['POST'])
    @admin_required
    def delete_report(report_id):
        report = db.session.query(VerificationReport).get_or_404(report_id)
        cafe = report.cafe
        db.session.delete(report)
        remaining = db.session.query(VerificationReport).filter(
            VerificationReport.cafe_id == cafe.id,
            VerificationReport.is_processed == False
        ).count()
        if remaining == 0 and cafe.verification_status == 'Community Reported':
            cafe.verification_status = 'Recently Checked'
        db.session.commit()
        flash("Verification report dismissed.", "info")
        return redirect(url_for('admin_dashboard'))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)