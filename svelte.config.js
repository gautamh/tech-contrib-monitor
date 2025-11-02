import adapter from '@sveltejs/adapter-static';

const dev = process.argv.includes('dev');
const isTest = process.env.CI === 'true';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    kit: {
        adapter: adapter({
            pages: 'build',
            assets: 'build',
            fallback: null,
            precompress: false
        }),
        paths: {
            base: dev || isTest ? '' : '/tech-contrib-site'
        }
    }
};

export default config;
