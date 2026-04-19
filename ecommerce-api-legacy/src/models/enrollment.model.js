function createEnrollmentRepository(db) {
    return {
        create(userId, courseId) {
            return new Promise((resolve, reject) => {
                db.run(
                    "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
                    [userId, courseId],
                    function(err) {
                        if (err) reject(err);
                        else resolve(this.lastID);
                    }
                );
            });
        },

        findByCourse(courseId) {
            return new Promise((resolve, reject) => {
                db.all(
                    "SELECT id, user_id, course_id FROM enrollments WHERE course_id = ?",
                    [courseId],
                    (err, enrollments) => {
                        if (err) reject(err);
                        else resolve(enrollments || []);
                    }
                );
            });
        }
    };
}

module.exports = { createEnrollmentRepository };
