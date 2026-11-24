module.exports = {
  ci: {
    collect: {
      staticDistDir: "./_site",
      url: [
        "http://localhost/",
        "http://localhost/projects/",
        "http://localhost/articles/building-with-nature-in-mind/",
      ],
      numberOfRuns: 2,
      settings: {
        chromeFlags: "--no-sandbox --disable-dev-shm-usage",
      },
    },
    assert: {
      assertions: {
        "categories:performance": ["warn", { minScore: 0.8 }],
        "largest-contentful-paint": ["warn", { maxNumericValue: 4000 }],
        "cumulative-layout-shift": ["warn", { maxNumericValue: 0.25 }],
        "total-byte-weight": ["warn", { maxNumericValue: 2000000 }],
      },
    },
    upload: {
      target: "filesystem",
      outputDir: "./artifacts/lighthouse/mobile",
    },
  },
};
