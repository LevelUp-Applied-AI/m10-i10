/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a self-contained server bundle under `.next/standalone/` that
  // the multi-stage Dockerfile's runner can ship without node_modules.
  // This is what keeps the runner image under the M10 rubric's 400 MB
  // target — without it, copying full node_modules pushes the image
  // past 600 MB even on alpine.
  // https://nextjs.org/docs/pages/api-reference/next-config-js/output
  output: 'standalone',
};

module.exports = nextConfig;
