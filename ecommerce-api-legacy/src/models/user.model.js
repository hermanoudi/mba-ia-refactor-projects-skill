function createUserRepository(db) {
    return {
        findByEmail(email) {
            return new Promise((resolve, reject) => {
                db.get("SELECT id FROM users WHERE email = ?", [email], (err, user) => {
                    if (err) reject(err);
                    else resolve(user);
                });
            });
        },

        create(name, email, passwordHash) {
            return new Promise((resolve, reject) => {
                db.run(
                    "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
                    [name, email, passwordHash],
                    function(err) {
                        if (err) reject(err);
                        else resolve(this.lastID);
                    }
                );
            });
        },

        delete(userId) {
            return new Promise((resolve, reject) => {
                db.run("DELETE FROM users WHERE id = ?", [userId], (err) => {
                    if (err) reject(err);
                    else resolve();
                });
            });
        }
    };
}

module.exports = { createUserRepository };
