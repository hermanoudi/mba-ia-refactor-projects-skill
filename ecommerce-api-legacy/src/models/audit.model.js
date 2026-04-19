function createAuditRepository(db) {
    return {
        log(action) {
            return new Promise((resolve, reject) => {
                db.run(
                    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                    [action],
                    function(err) {
                        if (err) reject(err);
                        else resolve(this.lastID);
                    }
                );
            });
        }
    };
}

module.exports = { createAuditRepository };
