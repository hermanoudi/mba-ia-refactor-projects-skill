const express = require('express');

function createAdminRoutes(adminController, logger) {
    const router = express.Router();

    router.get('/api/admin/financial-report', async (req, res, next) => {
        try {
            const report = await adminController.getFinancialReport();
            res.json(report);
        } catch (err) {
            logger.error('Financial report error', err);
            next(err);
        }
    });

    return router;
}

module.exports = { createAdminRoutes };
