function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    const message = err.message || 'Internal server error';

    console.error(`[ERROR] ${status}: ${message}`, err.stack);

    if (status === 400) {
        return res.status(400).json({ error: message });
    }

    if (status === 404) {
        return res.status(404).json({ error: 'Resource not found' });
    }

    res.status(500).json({ error: 'Internal server error' });
}

module.exports = { errorHandler };
