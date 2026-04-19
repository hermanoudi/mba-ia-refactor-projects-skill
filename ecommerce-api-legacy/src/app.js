const express = require('express');
const config = require('./config/settings');
const { initializeDatabase } = require('./database/db');
const { createUserRepository } = require('./models/user.model');
const { createCourseRepository } = require('./models/course.model');
const { createEnrollmentRepository } = require('./models/enrollment.model');
const { createPaymentRepository } = require('./models/payment.model');
const { createAuditRepository } = require('./models/audit.model');
const { createCheckoutController } = require('./controllers/checkout.controller');
const { createAdminController } = require('./controllers/admin.controller');
const { createCheckoutRoutes } = require('./routes/checkout.routes');
const { createAdminRoutes } = require('./routes/admin.routes');
const { createUserRoutes } = require('./routes/user.routes');
const { errorHandler } = require('./middleware/error.handler');

const logger = {
    info: (msg) => console.log(`[INFO] ${msg}`),
    error: (msg, err) => console.error(`[ERROR] ${msg}`, err)
};

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = await initializeDatabase();

    const userRepository = createUserRepository(db);
    const courseRepository = createCourseRepository(db);
    const enrollmentRepository = createEnrollmentRepository(db);
    const paymentRepository = createPaymentRepository(db);
    const auditRepository = createAuditRepository(db);

    const repositories = {
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository
    };

    const checkoutController = createCheckoutController(repositories, logger);
    const adminController = createAdminController(db, logger);

    app.use(createCheckoutRoutes(checkoutController, logger));
    app.use(createAdminRoutes(adminController, logger));
    app.use(createUserRoutes(userRepository, logger));

    app.use(errorHandler);

    return app;
}

async function main() {
    try {
        const app = await createApp();
        app.listen(config.port, () => {
            console.log(`LMS API running on port ${config.port}...`);
        });
    } catch (err) {
        console.error('Failed to start application', err);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { createApp };
