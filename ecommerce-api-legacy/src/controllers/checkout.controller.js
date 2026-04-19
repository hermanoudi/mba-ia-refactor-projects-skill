const { hashPassword } = require('../utils/crypto');
const VISA_CARD_PREFIX = '4';

function createCheckoutController(repositories, logger) {
    const { userRepository, courseRepository, enrollmentRepository, paymentRepository, auditRepository } = repositories;

    async function processCheckout(userName, email, password, courseId, cardNumber) {
        if (!cardNumber.startsWith(VISA_CARD_PREFIX)) {
            throw new Error('Payment denied: Invalid card');
        }

        const course = await courseRepository.findById(courseId);
        if (!course) {
            throw new Error('Course not found');
        }

        let user = await userRepository.findByEmail(email);
        if (!user) {
            const passwordHash = hashPassword(password || '123456');
            user = { id: await userRepository.create(userName, email, passwordHash) };
        }

        const enrollmentId = await enrollmentRepository.create(user.id, courseId);
        const paymentId = await paymentRepository.create(enrollmentId, course.price, 'PAID');

        await auditRepository.log(`Checkout curso ${courseId} por ${user.id}`);
        logger.info(`Payment processed for enrollment ${enrollmentId}`);

        return { enrollmentId, paymentId, message: 'Success' };
    }

    return { processCheckout };
}

module.exports = { createCheckoutController };
