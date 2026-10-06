import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the Base44 preview origin to fetch dev assets / HMR (Next gates dev requests by origin).
  allowedDevOrigins: process.env.BASE44_PUBLIC_HOST_SUFFIX
    ? [`https://3000-${process.env.BASE44_PUBLIC_HOST_SUFFIX}`]
    : undefined,
};

export default nextConfig;
