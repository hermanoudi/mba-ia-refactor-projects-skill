const HASH_ITERATIONS = 10000;

function hashPassword(password) {
    let hash = "";
    for(let i = 0; i < HASH_ITERATIONS; i++) {
        hash += Buffer.from(password).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}

module.exports = { hashPassword };
