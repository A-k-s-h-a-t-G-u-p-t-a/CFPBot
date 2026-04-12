"use client";

import { FaXTwitter, FaInstagram, FaLinkedin } from "react-icons/fa6";

export default function Footer() {
  return (
    <div className="relative bg-black text-gray-300 pt-12 px-6 md:px-20 border-t border-blue-900 overflow-hidden">
      {/* Footer content */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12 relative z-10">
        {/* Logo and tagline */}
        <div>
          <h2 className="text-2xl font-bold text-white">Metric<span className="text-blue-500">Lens</span></h2>
          <p className="text-sm mt-2">advanced chatbot insights for business metrics</p>
          <div className="flex gap-4 mt-6 text-blue-400 text-xl">
            <FaXTwitter className="hover:text-white cursor-pointer" />
            <FaInstagram className="hover:text-white cursor-pointer" />
            <FaLinkedin className="hover:text-white cursor-pointer" />
          </div>
        </div>

        {/* Capabilities */}
        <div>
          <h3 className="text-white font-semibold mb-4">Capabilities</h3>
          <ul className="space-y-2 text-sm">
            <li><span className="opacity-50">Understand changes</span></li>
            <li><span className="opacity-50">Compare metrics</span></li>
            <li><span className="opacity-50">Break down drivers</span></li>
            <li><span className="opacity-50">Summarize trends</span></li>
            <li><span className="opacity-50">Reference sources</span></li>
          </ul>
        </div>

        {/* Resources */}
        <div>
          <h3 className="text-white font-semibold mb-4">Resources</h3>
          <ul className="space-y-2 text-sm">
            <li><span className="opacity-50">Docs</span></li>
            <li><span className="opacity-50">Data sources</span></li>
            <li><span className="opacity-50">Privacy policy</span></li>
            <li><span className="opacity-50">Security</span></li>
            <li><span className="opacity-50">Contact</span></li>
          </ul>
        </div>
      </div>
    
      {/* Background gradient */}
       <div className="w-full text-center mt-20 select-none pointer-events-none">
            <h1 className="text-[100px] md:text-[150px] font-extrabold bg-gradient-to-b from-blue-500 via-blue-700 to-black text-transparent bg-clip-text tracking-tight opacity-50">
                METRICLENS
            </h1>
        </div>

      {/* Copyright */}
      <div className="relative z-10 mt-12 border-t border-gray-800 pt-6 text-sm text-center text-gray-500">
        © 2026 MetricLens. All rights reserved.
      </div>

    </div>
  );
}
