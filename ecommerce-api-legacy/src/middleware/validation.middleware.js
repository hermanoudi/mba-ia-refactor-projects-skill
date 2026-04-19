function validateCheckoutRequest(req, res, next) {
    const { usr, eml, pwd, c_id, card } = req.body;

    if (!usr || typeof usr !== 'string' || usr.trim().length < 2) {
        return res.status(400).json({ error: 'Invalid user name (min 2 characters)' });
    }

    if (!eml || !isValidEmail(eml)) {
        return res.status(400).json({ error: 'Invalid email format' });
    }

    if (!c_id || isNaN(c_id)) {
        return res.status(400).json({ error: 'Course ID must be a number' });
    }

    if (!card || !isValidCardNumber(card)) {
        return res.status(400).json({ error: 'Invalid card number' });
    }

    next();
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidCardNumber(card) {
    return card.length >= 13 && card.length <= 19 && /^\d+$/.test(card);
}

module.exports = { validateCheckoutRequest };
