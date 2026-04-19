const sqlite3 = require('sqlite3').verbose();

function initializeDatabase() {
    const db = new sqlite3.Database(':memory:');

    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)", (err) => {
                if (err) reject(err);
            });

            db.run("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)", (err) => {
                if (err) reject(err);
            });

            db.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)", (err) => {
                if (err) reject(err);
            });

            db.run("CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)", (err) => {
                if (err) reject(err);
            });

            db.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)", (err) => {
                if (err) reject(err);
            });

            db.run("INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')");
            db.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
            db.run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
            db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')", (err) => {
                if (err) reject(err);
                else resolve(db);
            });
        });
    });
}

module.exports = { initializeDatabase };
