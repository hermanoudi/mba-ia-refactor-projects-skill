const express = require('express');
const { validateCheckoutRequest } = require('../middleware/validation.middleware');

function createCheckoutRoutes(checkoutController, logger) {
    const router = express.Router();

    router.post('/api/checkout', validateCheckoutRequest, async (req, res, next) => {
        try {
            const { usr, eml, pwd, c_id, card } = req.body;
            const result = await checkoutController.processCheckout(usr, eml, pwd, c_id, card);
            res.status(200).json({ msg: result.message, enrollment_id: result.enrollmentId });
        } catch (err) {
            logger.error('Checkout error', err);
            if (err.message.includes('Payment denied')) {
                return res.status(400).json({ error: err.message });
            }
            if (err.message.includes('Course not found')) {
                return res.status(404).json({ error: err.message });
            }
            next(err);
        }
    });

    return router;
}

module.exports = { createCheckoutRoutes };
