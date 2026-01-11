/**
 * Home / Landing Page
 * Modern dark-themed landing page showcasing AI Agent capabilities
 * with animated tool demonstrations
 */

'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, useInView, AnimatePresence } from 'framer-motion';
import { ROUTES, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import {
  Mail, Cloud, FileText, BarChart3, Phone, Sparkles,
  Send, Bot, User, ArrowRight, Play, ChevronRight,
  Database, Zap, Shield, Clock
} from 'lucide-react';

// Tool Demo Data
const toolDemos = [
  {
    id: 'email',
    name: 'Gmail Integration',
    icon: Mail,
    color: 'from-red-500 to-pink-500',
    bgGlow: 'bg-red-500/20',
    description: 'Send emails, read inbox, and manage communications directly through AI',
    demo: {
      query: "Send an email to john@company.com with subject 'Monthly Sales Report' and attach the latest analytics summary",
      response: "I've sent the email to john@company.com with the Monthly Sales Report. The email includes:\n\n📧 **Email Sent Successfully**\n- To: john@company.com\n- Subject: Monthly Sales Report\n- Attachment: analytics_summary_jan2025.pdf\n\nThe recipient will receive it shortly.",
      steps: ['Composing email...', 'Attaching analytics...', 'Sending...', 'Delivered!']
    }
  },
  {
    id: 'gdrive',
    name: 'Google Drive',
    icon: Cloud,
    color: 'from-blue-500 to-cyan-500',
    bgGlow: 'bg-blue-500/20',
    description: 'Search, read, and manage files in your Google Drive seamlessly',
    demo: {
      query: "Find all documents related to 'Q4 Budget' in my Drive and summarize them",
      response: "Found 3 documents matching 'Q4 Budget':\n\n📁 **Q4_Budget_2024.xlsx**\n- Total Budget: $450,000\n- Spent: $387,500 (86%)\n- Remaining: $62,500\n\n📁 **Q4_Budget_Proposal.docx**\n- Key highlights: Marketing expansion, New hires\n\n📁 **Q4_Budget_Review.pdf**\n- Status: Approved by Finance",
      steps: ['Searching Drive...', 'Reading files...', 'Analyzing content...', 'Summary ready!']
    }
  },
  {
    id: 'notion',
    name: 'Notion Workspace',
    icon: FileText,
    color: 'from-gray-600 to-gray-800',
    bgGlow: 'bg-gray-500/20',
    description: 'Access and manage your Notion pages, databases, and notes',
    demo: {
      query: "Create a new project page in Notion for 'Website Redesign' with tasks and timeline",
      response: "Created new Notion page:\n\n📝 **Website Redesign Project**\n\n**Tasks Created:**\n- [ ] Design mockups (Due: Jan 20)\n- [ ] Frontend development (Due: Feb 5)\n- [ ] Backend integration (Due: Feb 15)\n- [ ] Testing & QA (Due: Feb 25)\n- [ ] Launch (Due: Mar 1)\n\n🔗 Page link: notion.so/website-redesign",
      steps: ['Creating page...', 'Adding tasks...', 'Setting timeline...', 'Page created!']
    }
  },
  {
    id: 'analytics',
    name: 'AI Analytics',
    icon: BarChart3,
    color: 'from-emerald-500 to-teal-500',
    bgGlow: 'bg-emerald-500/20',
    description: 'Generate charts, insights, and visualizations from your data',
    demo: {
      query: "Show me a chart of sales trends for the last 6 months with predictions",
      response: "Here's your sales analysis:\n\n📊 **6-Month Sales Trend**\n\n```\nJul: ████████░░ $82K\nAug: █████████░ $91K\nSep: ███████░░░ $78K\nOct: ██████████ $105K\nNov: ███████████ $118K\nDec: ████████████ $142K\n```\n\n📈 **Prediction:** Jan 2025 estimated at $156K (+10%)\n\n💡 **Insight:** Strong growth trend, Q4 peak season",
      steps: ['Fetching data...', 'Analyzing trends...', 'Generating chart...', 'Predictions ready!']
    }
  },
  {
    id: 'retellai',
    name: 'Retell AI Voice',
    icon: Phone,
    color: 'from-purple-500 to-violet-500',
    bgGlow: 'bg-purple-500/20',
    description: 'Make AI-powered voice calls and automate phone communications',
    demo: {
      query: "Call the supplier at +1-555-0123 to confirm our order #12345 delivery date",
      response: "Voice call completed:\n\n📞 **Call Summary**\n- Duration: 2:34\n- Recipient: ABC Supplies (+1-555-0123)\n\n**Key Points:**\n✅ Order #12345 confirmed\n✅ Delivery: January 18, 2025\n✅ Tracking number sent to email\n\n🎙️ Call recording saved to your account",
      steps: ['Initiating call...', 'Connected...', 'Discussing order...', 'Call complete!']
    }
  }
];

// Animated typing effect component
function TypeWriter({ text, speed = 30, onComplete }: { text: string; speed?: number; onComplete?: () => void }) {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, speed);
      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentIndex, text, speed, onComplete]);

  return <span>{displayText}</span>;
}

// Tool Demo Card Component
function ToolDemoCard({ tool, index }: { tool: typeof toolDemos[0]; index: number }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showResponse, setShowResponse] = useState(false);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const startDemo = () => {
    setIsPlaying(true);
    setCurrentStep(0);
    setShowResponse(false);

    // Animate through steps
    tool.demo.steps.forEach((_, i) => {
      setTimeout(() => {
        setCurrentStep(i + 1);
        if (i === tool.demo.steps.length - 1) {
          setTimeout(() => setShowResponse(true), 500);
        }
      }, (i + 1) * 800);
    });
  };

  const resetDemo = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setShowResponse(false);
  };

  const Icon = tool.icon;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      className="relative group"
    >
      {/* Glow Effect */}
      <div className={`absolute -inset-1 ${tool.bgGlow} rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

      <div className="relative bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 hover:border-gray-700 transition-all duration-300">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tool.color} flex items-center justify-center`}>
              <Icon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{tool.name}</h3>
              <p className="text-sm text-gray-400">{tool.description}</p>
            </div>
          </div>
        </div>

        {/* Demo Area */}
        <div className="bg-gray-950/50 rounded-xl p-4 min-h-[300px]">
          {/* User Query */}
          <div className="flex items-start space-x-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="bg-blue-600/20 rounded-lg rounded-tl-none p-3 flex-1">
              <p className="text-sm text-gray-200">{tool.demo.query}</p>
            </div>
          </div>

          {/* Processing Steps */}
          {isPlaying && !showResponse && (
            <div className="flex items-center space-x-3 mb-4 ml-11">
              <div className="flex space-x-1">
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 bg-emerald-500 rounded-full"
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </div>
              <span className="text-sm text-emerald-400">
                {tool.demo.steps[currentStep - 1] || tool.demo.steps[0]}
              </span>
            </div>
          )}

          {/* AI Response */}
          <AnimatePresence>
            {showResponse && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start space-x-3"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-800/50 rounded-lg rounded-tl-none p-3 flex-1">
                  <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans">
                    {tool.demo.response}
                  </pre>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Play Button */}
          {!isPlaying && (
            <motion.button
              onClick={startDemo}
              className="absolute bottom-6 right-6 flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg font-medium hover:opacity-90 transition-opacity"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Play className="w-4 h-4" />
              <span>Watch Demo</span>
            </motion.button>
          )}

          {/* Reset Button */}
          {showResponse && (
            <motion.button
              onClick={resetDemo}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute bottom-6 right-6 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Replay Demo
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Stats Counter Component
function StatCounter({ value, label, suffix = '' }: { value: number; label: string; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (isInView) {
      const duration = 2000;
      const steps = 60;
      const increment = value / steps;
      let current = 0;
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          setCount(value);
          clearInterval(timer);
        } else {
          setCount(Math.floor(current));
        }
      }, duration / steps);
      return () => clearInterval(timer);
    }
  }, [isInView, value]);

  return (
    <div ref={ref} className="text-center">
      <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
        {count}{suffix}
      </div>
      <div className="text-gray-400 mt-2">{label}</div>
    </div>
  );
}

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const heroRef = useRef(null);
  const isHeroInView = useInView(heroRef, { once: true });

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push(ROUTES.DASHBOARD);
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <motion.div
          className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-x-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gray-950/80 backdrop-blur-md border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">{APP_METADATA.NAME}</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href={ROUTES.LOGIN}
              className="text-gray-400 hover:text-white transition-colors font-medium"
            >
              Login
            </Link>
            <Link
              href={ROUTES.SIGNUP}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-5 py-2 rounded-lg hover:opacity-90 transition-opacity font-medium"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isHeroInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8 }}
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-2 mb-8"
            >
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-emerald-400">AI-Powered Automation</span>
            </motion.div>

            {/* Main Heading */}
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight">
              Your AI Agent That
              <br />
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Connects Everything
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-gray-400 max-w-3xl mx-auto mb-10">
              One intelligent agent that integrates with Gmail, Google Drive, Notion, Analytics,
              and more. Ask in natural language, get things done automatically.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
              <Link href={ROUTES.SIGNUP}>
                <motion.button
                  className="flex items-center justify-center space-x-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span>Start Free</span>
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
              <Link href="#tools">
                <motion.button
                  className="flex items-center justify-center space-x-2 border border-gray-700 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-gray-800/50 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Play className="w-5 h-5" />
                  <span>See It In Action</span>
                </motion.button>
              </Link>
            </div>

            {/* Hero Visual - Chat Interface Preview */}
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="relative max-w-4xl mx-auto"
            >
              <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-blue-500/20 rounded-3xl blur-2xl" />
              <div className="relative bg-gray-900/90 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 shadow-2xl">
                {/* Chat Header */}
                <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-gray-800">
                  <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold">StoreLite AI Agent</h3>
                    <p className="text-sm text-emerald-400">Online • Ready to help</p>
                  </div>
                </div>

                {/* Chat Messages */}
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-blue-600/20 rounded-lg rounded-tl-none p-3">
                      <p className="text-sm">Send yesterday&apos;s sales report to the team via email and update Notion</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gray-800/50 rounded-lg rounded-tl-none p-3 flex-1">
                      <p className="text-sm text-gray-200">
                        Done! I&apos;ve completed both tasks:
                      </p>
                      <div className="mt-3 space-y-2">
                        <div className="flex items-center space-x-2 text-sm">
                          <Mail className="w-4 h-4 text-red-400" />
                          <span className="text-gray-300">Email sent to 5 team members</span>
                          <span className="text-emerald-400">✓</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <FileText className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-300">Notion &quot;Daily Reports&quot; updated</span>
                          <span className="text-emerald-400">✓</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Input Area */}
                <div className="mt-6 flex items-center space-x-3">
                  <div className="flex-1 bg-gray-800/50 rounded-lg px-4 py-3 text-gray-400 text-sm">
                    Ask me anything...
                  </div>
                  <button className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-lg flex items-center justify-center">
                    <Send className="w-5 h-5 text-white" />
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <StatCounter value={5} label="Integrated Tools" suffix="+" />
            <StatCounter value={10000} label="Tasks Automated" suffix="+" />
            <StatCounter value={99} label="Uptime" suffix="%" />
            <StatCounter value={24} label="Support" suffix="/7" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Why Choose <span className="text-emerald-400">StoreLite</span>?
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Built for businesses that want to automate workflows without complexity
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Database, title: "Your Data, Your Control", desc: "Connect your own database or use our platform" },
              { icon: Zap, title: "Instant Automation", desc: "Set up workflows in seconds, not hours" },
              { icon: Shield, title: "Enterprise Security", desc: "OAuth 2.0 & encrypted connections" },
              { icon: Clock, title: "24/7 Scheduling", desc: "Automate tasks at any time" },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-emerald-500/50 transition-colors"
              >
                <feature.icon className="w-10 h-10 text-emerald-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tool Demos Section */}
      <section id="tools" className="py-20 bg-gray-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Powerful <span className="text-emerald-400">Integrations</span>
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              See how our AI agent connects with your favorite tools. Click &quot;Watch Demo&quot; to see it in action.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-8">
            {toolDemos.map((tool, index) => (
              <ToolDemoCard key={tool.id} tool={tool} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              How It <span className="text-emerald-400">Works</span>
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Connect Your Tools", desc: "Link Gmail, Drive, Notion, and more with secure OAuth" },
              { step: "02", title: "Ask in Natural Language", desc: "Simply describe what you want done - no coding needed" },
              { step: "03", title: "Watch It Work", desc: "Our AI executes the task and reports back with results" },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative text-center"
              >
                <div className="text-6xl font-bold text-emerald-500/20 mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.desc}</p>
                {i < 2 && (
                  <ChevronRight className="hidden md:block absolute top-8 -right-4 w-8 h-8 text-gray-700" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-3xl blur-2xl" />
            <div className="relative bg-gray-900/80 border border-gray-800 rounded-2xl p-12">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Ready to Automate Your Workflow?
              </h2>
              <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
                Join thousands of businesses using StoreLite to save time and boost productivity.
              </p>
              <Link href={ROUTES.SIGNUP}>
                <motion.button
                  className="inline-flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:opacity-90 transition-opacity"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span>Get Started Free</span>
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-semibold">{APP_METADATA.NAME}</span>
            </div>
            <p className="text-gray-500 text-sm">
              © 2025 {APP_METADATA.NAME}. AI-Powered Inventory & Workflow Automation.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
