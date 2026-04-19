const express = require('express');

function createUserRoutes(userRepository, logger) {
    const router = express.Router();

    router.delete('/api/users/:id', async (req, res, next) => {
        try {
            const userId = parseInt(req.params.id, 10);
            if (isNaN(userId)) {
                return res.status(400).json({ error: 'Invalid user ID' });
            }
            await userRepository.delete(userId);
            res.json({ message: 'User deleted successfully' });
        } catch (err) {
            logger.error('Delete user error', err);
            next(err);
        }
    });

    return router;
}

module.exports = { createUserRoutes };
