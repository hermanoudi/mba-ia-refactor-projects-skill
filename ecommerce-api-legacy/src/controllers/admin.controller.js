function createAdminController(db, logger) {
    async function getFinancialReport() {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT
                    c.id as course_id,
                    c.title as course_title,
                    u.name as student_name,
                    u.email as student_email,
                    p.amount as paid_amount,
                    p.status as payment_status
                FROM courses c
                LEFT JOIN enrollments e ON c.id = e.course_id
                LEFT JOIN users u ON e.user_id = u.id
                LEFT JOIN payments p ON e.id = p.enrollment_id
                ORDER BY c.id, u.name
            `;

            db.all(query, [], (err, rows) => {
                if (err) {
                    logger.error('Financial report query failed', err);
                    return reject(err);
                }

                const report = {};
                rows.forEach(row => {
                    const courseId = row.course_id;
                    if (!report[courseId]) {
                        report[courseId] = {
                            course: row.course_title,
                            revenue: 0,
                            students: []
                        };
                    }
                    if (row.student_name && row.payment_status === 'PAID') {
                        report[courseId].revenue += row.paid_amount || 0;
                        report[courseId].students.push({
                            student: row.student_name,
                            paid: row.paid_amount || 0
                        });
                    }
                });

                resolve(Object.values(report));
            });
        });
    }

    return { getFinancialReport };
}

module.exports = { createAdminController };
