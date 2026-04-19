function createCourseRepository(db) {
    return {
        findById(courseId) {
            return new Promise((resolve, reject) => {
                db.get(
                    "SELECT id, title, price FROM courses WHERE id = ? AND active = 1",
                    [courseId],
                    (err, course) => {
                        if (err) reject(err);
                        else resolve(course);
                    }
                );
            });
        },

        findAll() {
            return new Promise((resolve, reject) => {
                db.all("SELECT id, title, price FROM courses", [], (err, courses) => {
                    if (err) reject(err);
                    else resolve(courses);
                });
            });
        }
    };
}

module.exports = { createCourseRepository };
