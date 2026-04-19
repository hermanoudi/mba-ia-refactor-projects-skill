function createPaymentRepository(db) {
    return {
        create(enrollmentId, amount, status) {
            return new Promise((resolve, reject) => {
                db.run(
                    "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
                    [enrollmentId, amount, status],
                    function(err) {
                        if (err) reject(err);
                        else resolve(this.lastID);
                    }
                );
            });
        },

        findByEnrollment(enrollmentId) {
            return new Promise((resolve, reject) => {
                db.get(
                    "SELECT amount, status FROM payments WHERE enrollment_id = ?",
                    [enrollmentId],
                    (err, payment) => {
                        if (err) reject(err);
                        else resolve(payment);
                    }
                );
            });
        },

        findByEnrollmentWithUser(enrollmentId) {
            return new Promise((resolve, reject) => {
                db.get(
                    "SELECT p.amount, p.status, u.name, u.email FROM payments p JOIN enrollments e ON p.enrollment_id = e.id JOIN users u ON e.user_id = u.id WHERE p.enrollment_id = ?",
                    [enrollmentId],
                    (err, payment) => {
                        if (err) reject(err);
                        else resolve(payment);
                    }
                );
            });
        }
    };
}

module.exports = { createPaymentRepository };
