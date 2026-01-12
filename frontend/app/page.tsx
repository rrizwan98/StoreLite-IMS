/**
 * Home / Landing Page
 * Modern dark-themed landing page showcasing AI Agent capabilities
 * with animated tool demonstrations
 */

'use client';

import Link from 'next/link';
import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, useInView, AnimatePresence } from 'framer-motion';
import { ROUTES, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import {
  Mail, Cloud, FileText, BarChart3, Phone, Sparkles,
  Send, Bot, User, ArrowRight, Play, ChevronRight,
  Database, Zap, Shield, Clock, X, MessageSquare,
  Calendar, Wrench, CheckCircle, Users, Globe, Lock,
  MessageCircle, Cpu, Timer
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

// Tool Demo Card Component - ChatKit-like inline demo (no popup)
function ToolDemoCard({
  tool,
  index,
}: {
  tool: typeof toolDemos[0];
  index: number;
}) {
  // Demo states: idle -> typing_in_input -> sent -> thinking -> streaming -> complete
  const [demoState, setDemoState] = useState<'idle' | 'typing_in_input' | 'sent' | 'thinking' | 'streaming' | 'complete'>('idle');
  const [inputText, setInputText] = useState(''); // Text in input box
  const [streamedResponse, setStreamedResponse] = useState('');
  const [currentStep, setCurrentStep] = useState(0);
  const ref = useRef(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const query = tool.demo.query;
  const response = tool.demo.response;
  const steps = tool.demo.steps;

  // Auto-scroll chat area
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [inputText, streamedResponse, demoState]);

  // Start demo
  const startDemo = () => {
    setDemoState('typing_in_input');
    setInputText('');
    setStreamedResponse('');
    setCurrentStep(0);
  };

  // Reset demo
  const resetDemo = () => {
    setDemoState('idle');
    setInputText('');
    setStreamedResponse('');
    setCurrentStep(0);
  };

  // Phase 1: Typing in input box
  useEffect(() => {
    if (demoState !== 'typing_in_input') return;

    let i = 0;
    const interval = setInterval(() => {
      if (i < query.length) {
        setInputText(query.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        // Wait then "send" the message
        setTimeout(() => {
          setDemoState('sent');
          // After message appears in chat, start thinking
          setTimeout(() => {
            setDemoState('thinking');
          }, 300);
        }, 500);
      }
    }, 25);

    return () => clearInterval(interval);
  }, [demoState, query]);

  // Phase 2: Thinking/processing steps
  useEffect(() => {
    if (demoState !== 'thinking') return;

    let stepIdx = 0;
    setCurrentStep(0);

    const stepInterval = setInterval(() => {
      stepIdx++;
      if (stepIdx < steps.length) {
        setCurrentStep(stepIdx);
      } else {
        clearInterval(stepInterval);
        // Start streaming after all thinking steps
        setTimeout(() => setDemoState('streaming'), 400);
      }
    }, 700);

    return () => clearInterval(stepInterval);
  }, [demoState, steps.length]);

  // Phase 3: Streaming response
  useEffect(() => {
    if (demoState !== 'streaming') return;

    let i = 0;
    const interval = setInterval(() => {
      if (i < response.length) {
        setStreamedResponse(response.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        setDemoState('complete');
      }
    }, 10);

    return () => clearInterval(interval);
  }, [demoState, response]);

  const Icon = tool.icon;
  const showMessageInChat = demoState === 'sent' || demoState === 'thinking' || demoState === 'streaming' || demoState === 'complete';

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

      <div className="relative bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden hover:border-gray-700 transition-all duration-300">
        {/* ChatKit-style Header */}
        <div className="bg-gray-900 border-b border-gray-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${tool.color} flex items-center justify-center`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{tool.name}</h3>
              <p className="text-xs text-gray-500">{tool.description.slice(0, 40)}...</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-xs text-emerald-400">Online</span>
          </div>
        </div>

        {/* ChatKit-style Chat Area */}
        <div
          ref={chatRef}
          className="h-[280px] overflow-y-auto p-4 space-y-3 bg-[#0a0a0f]"
          style={{
            backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.03) 0%, transparent 50%)'
          }}
        >
          {/* Initial state - show prompt */}
          {demoState === 'idle' && (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${tool.color} flex items-center justify-center mb-3`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <h4 className="text-white font-medium mb-1 text-sm">Try {tool.name}</h4>
              <p className="text-gray-500 text-xs mb-4 max-w-[220px]">
                See how this integration works
              </p>
              <motion.button
                onClick={startDemo}
                className={`flex items-center space-x-2 px-4 py-2 bg-gradient-to-r ${tool.color} text-white rounded-lg font-medium text-sm shadow-lg`}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                <Play className="w-3.5 h-3.5" />
                <span>Watch Demo</span>
              </motion.button>
            </div>
          )}

          {/* User Message - shown after sent */}
          {showMessageInChat && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-end"
            >
              <div className="max-w-[85%]">
                <div className="bg-blue-600 text-white rounded-2xl rounded-br-sm px-3.5 py-2 text-sm">
                  {query}
                </div>
              </div>
            </motion.div>
          )}

          {/* Thinking/Processing indicator with steps */}
          {demoState === 'thinking' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start space-x-2"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="bg-gray-800/80 rounded-2xl rounded-bl-sm px-3.5 py-2.5">
                <div className="flex items-center space-x-2">
                  {/* Animated dots */}
                  <div className="flex space-x-0.5">
                    {[0, 1, 2].map(i => (
                      <motion.span
                        key={i}
                        className="w-1.5 h-1.5 bg-emerald-400 rounded-full"
                        animate={{
                          scale: [1, 1.3, 1],
                          opacity: [0.5, 1, 0.5]
                        }}
                        transition={{
                          duration: 0.6,
                          repeat: Infinity,
                          delay: i * 0.15
                        }}
                      />
                    ))}
                  </div>
                  <span className="text-xs text-gray-400">{steps[currentStep]}</span>
                </div>
              </div>
            </motion.div>
          )}

          {/* AI Response - streaming */}
          {(demoState === 'streaming' || demoState === 'complete') && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start space-x-2"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="max-w-[85%] bg-gray-800/80 rounded-2xl rounded-bl-sm px-3.5 py-2.5">
                <div className="text-sm text-gray-100 whitespace-pre-wrap leading-relaxed">
                  {streamedResponse}
                  {demoState === 'streaming' && (
                    <motion.span
                      className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 align-middle rounded-full"
                      animate={{ opacity: [1, 0, 1] }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                    />
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* ChatKit-style Input Area */}
        <div className="border-t border-gray-800 p-3 bg-gray-900">
          <div className="flex items-center space-x-2">
            <div className="flex-1 bg-gray-800 rounded-xl px-3.5 py-2.5 min-h-[40px] flex items-center">
              {demoState === 'typing_in_input' ? (
                <span className="text-white text-sm">
                  {inputText}
                  <motion.span
                    className="inline-block w-0.5 h-4 bg-white ml-0.5 align-middle rounded-full"
                    animate={{ opacity: [1, 0, 1] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  />
                </span>
              ) : demoState === 'idle' ? (
                <span className="text-gray-500 text-sm">Message AI Agent...</span>
              ) : (
                <span className="text-gray-500 text-sm">Message AI Agent...</span>
              )}
            </div>
            <motion.button
              className={`p-2.5 rounded-xl transition-all ${
                demoState === 'typing_in_input' && inputText.length > 0
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-800 text-gray-500'
              }`}
              animate={demoState === 'typing_in_input' && inputText.length > 0 ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 0.3 }}
            >
              <Send className="w-4 h-4" />
            </motion.button>
          </div>

          {/* Replay button */}
          {demoState === 'complete' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-center mt-2"
            >
              <button
                onClick={resetDemo}
                className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors flex items-center space-x-1"
              >
                <span>↻</span>
                <span>Replay Demo</span>
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// Hero Demo Video Component - Auto-play simulated chat screen with DB connection + multiple queries
function HeroDemoVideo() {
  const [phase, setPhase] = useState<'connecting' | 'connected' | 'typing' | 'sent' | 'thinking' | 'streaming' | 'complete' | 'pause'>('connecting');
  const [inputText, setInputText] = useState('');
  const [streamedResponse, setStreamedResponse] = useState('');
  const [queryIndex, setQueryIndex] = useState(0);
  const [messages, setMessages] = useState<{type: 'user' | 'bot', text: string}[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const chatRef = useRef<HTMLDivElement>(null);
  const queryIndexRef = useRef(queryIndex);

  // Keep ref in sync
  useEffect(() => {
    queryIndexRef.current = queryIndex;
  }, [queryIndex]);

  // 2 demo queries
  const demoQueries = [
    {
      query: "Show me products with low stock",
      response: "Found 3 products with low stock:\n\n📦 Wireless Mouse - 2 units\n📦 USB-C Hub - 4 units\n📦 Keyboard - 1 unit\n\n⚠️ Reorder recommended!",
      steps: ['Querying inventory...', 'Analyzing stock...', 'Done!']
    },
    {
      query: "What were today's total sales?",
      response: "Today's Sales Summary:\n\n💰 Total Revenue: $2,847.50\n📊 Orders: 23 completed\n🏆 Top Seller: iPhone Case (12 sold)\n\n📈 +18% vs yesterday!",
      steps: ['Fetching transactions...', 'Calculating totals...', 'Done!']
    }
  ];

  // Auto-scroll
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [inputText, streamedResponse, phase, messages]);

  // Single useEffect to manage all phase transitions
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    let interval: NodeJS.Timeout;

    const currentIdx = queryIndexRef.current;
    const query = demoQueries[currentIdx];

    if (phase === 'connecting') {
      timeout = setTimeout(() => setPhase('connected'), 2000);
    }
    else if (phase === 'connected') {
      timeout = setTimeout(() => setPhase('typing'), 1500);
    }
    else if (phase === 'typing') {
      let i = 0;
      interval = setInterval(() => {
        if (i < query.query.length) {
          setInputText(query.query.slice(0, i + 1));
          i++;
        } else {
          clearInterval(interval);
          timeout = setTimeout(() => setPhase('sent'), 400);
        }
      }, 35);
    }
    else if (phase === 'sent') {
      setMessages(prev => [...prev, { type: 'user', text: query.query }]);
      setInputText('');
      timeout = setTimeout(() => setPhase('thinking'), 300);
    }
    else if (phase === 'thinking') {
      let stepIdx = 0;
      setCurrentStep(0);
      interval = setInterval(() => {
        stepIdx++;
        if (stepIdx < query.steps.length) {
          setCurrentStep(stepIdx);
        } else {
          clearInterval(interval);
          timeout = setTimeout(() => setPhase('streaming'), 400);
        }
      }, 500);
    }
    else if (phase === 'streaming') {
      let i = 0;
      interval = setInterval(() => {
        if (i < query.response.length) {
          setStreamedResponse(query.response.slice(0, i + 1));
          i++;
        } else {
          clearInterval(interval);
          setMessages(prev => [...prev, { type: 'bot', text: query.response }]);
          setStreamedResponse('');
          setPhase('complete');
        }
      }, 12);
    }
    else if (phase === 'complete') {
      timeout = setTimeout(() => setPhase('pause'), 2000);
    }
    else if (phase === 'pause') {
      timeout = setTimeout(() => {
        const nextIndex = (currentIdx + 1) % demoQueries.length;
        if (nextIndex === 0) {
          setMessages([]);
        }
        setQueryIndex(nextIndex);
        setCurrentStep(0);
        setPhase('typing');
      }, 800);
    }

    return () => {
      if (timeout) clearTimeout(timeout);
      if (interval) clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, queryIndex]);

  const currentQuery = demoQueries[queryIndex];
  const isTypingOrLater = phase === 'typing' || phase === 'sent' || phase === 'thinking' || phase === 'streaming' || phase === 'complete' || phase === 'pause';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="max-w-4xl mx-auto"
    >
      {/* Large screen container - no header/footer */}
      <div className="relative">
        {/* Glow effect */}
        <div className="absolute -inset-3 bg-gradient-to-r from-emerald-500/30 via-cyan-500/25 to-blue-500/30 rounded-2xl blur-2xl" />

        {/* Screen */}
        <div className="relative bg-[#0a0a0f] border border-gray-700/50 rounded-2xl overflow-hidden shadow-2xl">
          {/* Chat Area */}
          <div
            ref={chatRef}
            className="h-[400px] sm:h-[450px] lg:h-[480px] overflow-y-auto p-5 sm:p-8 space-y-4"
            style={{
              backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.05) 0%, transparent 50%)'
            }}
          >
            {/* Database Connection Status */}
            {phase === 'connecting' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center justify-center h-full"
              >
                <div className="text-center">
                  <motion.div
                    className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center"
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    <Database className="w-8 h-8 text-emerald-400" />
                  </motion.div>
                  <div className="flex items-center justify-center space-x-2">
                    <motion.div
                      className="w-2 h-2 bg-emerald-400 rounded-full"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    />
                    <span className="text-gray-400 text-sm">Connecting to PostgreSQL...</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Connected Message */}
            {(phase === 'connected' || isTypingOrLater) && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start space-x-3"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-800/70 rounded-2xl rounded-bl-md px-4 py-3 max-w-[85%]">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full" />
                    <span className="text-xs text-emerald-400 font-medium">Connected to PostgreSQL</span>
                  </div>
                  <p className="text-sm text-gray-300">
                    Database ready! Ask me anything about your inventory.
                  </p>
                </div>
              </motion.div>
            )}

            {/* Previous Messages */}
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={msg.type === 'user' ? 'flex justify-end' : 'flex items-start space-x-3'}
              >
                {msg.type === 'bot' && (
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={msg.type === 'user'
                  ? 'max-w-[85%] bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3 text-sm shadow-lg shadow-blue-600/20'
                  : 'max-w-[85%] bg-gray-800/70 rounded-2xl rounded-bl-md px-4 py-3'
                }>
                  <p className={`text-sm whitespace-pre-wrap leading-relaxed ${msg.type === 'bot' ? 'text-gray-100' : ''}`}>
                    {msg.text}
                  </p>
                </div>
              </motion.div>
            ))}


            {/* Thinking indicator */}
            {phase === 'thinking' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start space-x-3"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-800/70 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      {[0, 1, 2].map(i => (
                        <motion.span
                          key={i}
                          className="w-2 h-2 bg-emerald-400 rounded-full"
                          animate={{
                            scale: [1, 1.3, 1],
                            opacity: [0.5, 1, 0.5]
                          }}
                          transition={{
                            duration: 0.6,
                            repeat: Infinity,
                            delay: i * 0.15
                          }}
                        />
                      ))}
                    </div>
                    <span className="text-xs text-gray-400">{currentQuery.steps[currentStep]}</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Streaming AI Response */}
            {phase === 'streaming' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start space-x-3"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="max-w-[85%] bg-gray-800/70 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="text-sm text-gray-100 whitespace-pre-wrap leading-relaxed">
                    {streamedResponse}
                    <motion.span
                      className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 align-middle rounded-full"
                      animate={{ opacity: [1, 0, 1] }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Input Area - Shows typing animation */}
          <div className="border-t border-gray-800/50 p-3 sm:p-4 bg-gray-900/60">
            <div className="flex items-center space-x-3">
              <div className="flex-1 bg-gray-800/90 rounded-xl px-4 py-3 min-h-[44px] flex items-center">
                {phase === 'typing' && inputText ? (
                  <span className="text-white text-sm">
                    {inputText}
                    <motion.span
                      className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 align-middle rounded-full"
                      animate={{ opacity: [1, 0, 1] }}
                      transition={{ duration: 0.5, repeat: Infinity }}
                    />
                  </span>
                ) : (
                  <span className="text-gray-500 text-sm">Ask about your inventory...</span>
                )}
              </div>
              <motion.div
                className={`p-3 rounded-xl transition-all ${
                  phase === 'typing' && inputText.length > 0
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                    : 'bg-gray-800 text-gray-500'
                }`}
                animate={phase === 'typing' && inputText.length > 0 ? { scale: [1, 1.05, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                <Send className="w-4 h-4" />
              </motion.div>
            </div>
          </div>
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

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
              Features
            </a>
            <a href="#tools" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
              Integrations
            </a>
            <a href="#schedule" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
              Schedule Tasks
            </a>
          </nav>

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
              Get Started Free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section ref={heroRef} className="relative pt-32 sm:pt-36 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Compact, Emotional Tagline */}
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-medium mb-2 text-gray-200">
              Your Database.{' '}
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent font-semibold">
                Now Intelligent.
              </span>
            </h1>

            <p className="text-sm text-gray-500 mb-8">
              Connect PostgreSQL. Ask in plain English. Get instant answers.
            </p>

            {/* Hero Demo Video - Large, auto-play simulated screen */}
            <HeroDemoVideo />

            {/* Benefits & CTA below hero */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-10 flex flex-col items-center"
            >
              {/* Quick Benefits */}
              <div className="flex flex-wrap justify-center gap-4 mb-6 text-sm text-gray-400">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Automate inventory queries</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Generate reports instantly</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span>Schedule recurring tasks</span>
                </div>
              </div>

              {/* Primary CTA */}
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <Link href={ROUTES.SIGNUP}>
                  <motion.button
                    className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-8 py-3.5 rounded-xl font-semibold hover:opacity-90 transition-opacity shadow-lg shadow-emerald-500/25"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Database className="w-5 h-5" />
                    <span>Connect My Database</span>
                  </motion.button>
                </Link>
                <div className="flex items-center space-x-2 text-gray-500 text-sm">
                  <Lock className="w-4 h-4" />
                  <span>256-bit encryption • SOC 2 compliant</span>
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
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="flex justify-center mb-3">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Wrench className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
              <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                5+
              </div>
              <div className="text-gray-400 mt-2">Integrated Tools</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-center"
            >
              <div className="flex justify-center mb-3">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                  <Cpu className="w-6 h-6 text-blue-400" />
                </div>
              </div>
              <StatCounter value={10000} label="Tasks Automated" suffix="+" />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-center"
            >
              <div className="flex justify-center mb-3">
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                  <Shield className="w-6 h-6 text-purple-400" />
                </div>
              </div>
              <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                99.9%
              </div>
              <div className="text-gray-400 mt-2">Uptime Guaranteed</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
              className="text-center"
            >
              <div className="flex justify-center mb-3">
                <div className="w-12 h-12 rounded-xl bg-orange-500/10 flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-orange-400" />
                </div>
              </div>
              <div className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                24/7
              </div>
              <div className="text-gray-400 mt-2">Support Available</div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
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

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Database, title: "Your Data, Your Control", desc: "Connect your own PostgreSQL database or use our secure cloud platform. Your data never leaves your infrastructure." },
              { icon: MessageSquare, title: "Natural Language Queries", desc: "Ask questions in plain English. No SQL knowledge required - just describe what you need." },
              { icon: Wrench, title: "Multi-Tool Automation", desc: "Connect Gmail, Drive, Notion and more. Automate workflows across all your favorite tools." },
              { icon: Calendar, title: "Task Scheduling", desc: "Schedule queries and automations for any date/time. Set recurring tasks that run automatically." },
              { icon: Shield, title: "Enterprise Security", desc: "OAuth 2.0, 256-bit encryption, and SOC 2 compliance. Your data is always protected." },
              { icon: Zap, title: "Instant Setup", desc: "Get started in under 5 minutes. No complex configuration or coding required." },
            ].map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-emerald-500/50 transition-colors group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-4 group-hover:from-emerald-500/30 group-hover:to-cyan-500/30 transition-colors">
                  <feature.icon className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
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

      {/* Schedule Your Tasks Section */}
      <section id="schedule" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Content */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
            >
              <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1.5 mb-6">
                <Timer className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400 text-sm font-medium">New Feature</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Schedule Your <span className="text-emerald-400">Tasks</span>
              </h2>
              <p className="text-gray-400 mb-8 leading-relaxed">
                Set up automated workflows that run on your schedule. Whether it&apos;s daily inventory reports,
                weekly sales summaries, or monthly analytics - let the AI handle it while you focus on growing
                your business.
              </p>
              <ul className="space-y-4 mb-8">
                {[
                  "Schedule queries for any date and time",
                  "Set up recurring tasks (daily, weekly, monthly)",
                  "Receive results via email or in-app notifications",
                  "Combine multiple tools in scheduled workflows"
                ].map((item, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-center space-x-3"
                  >
                    <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span className="text-gray-300">{item}</span>
                  </motion.li>
                ))}
              </ul>
              <Link href={ROUTES.SIGNUP}>
                <motion.button
                  className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold hover:opacity-90 transition-opacity"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Calendar className="w-5 h-5" />
                  <span>Start Scheduling</span>
                </motion.button>
              </Link>
            </motion.div>

            {/* Right: Calendar UI Preview */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative"
            >
              <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-3xl blur-2xl" />
              <div className="relative bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
                {/* Calendar Header */}
                <div className="bg-gray-800/50 px-6 py-4 border-b border-gray-700 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-emerald-400" />
                    <span className="font-medium">Schedule Task</span>
                  </div>
                  <span className="text-sm text-gray-400">January 2025</span>
                </div>

                {/* Mock Calendar Grid */}
                <div className="p-6">
                  <div className="grid grid-cols-7 gap-2 mb-4">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                      <div key={i} className="text-center text-xs text-gray-500 font-medium py-2">
                        {day}
                      </div>
                    ))}
                    {Array.from({ length: 35 }, (_, i) => {
                      const day = i - 2; // Start offset
                      const isValid = day >= 1 && day <= 31;
                      const isSelected = day === 15;
                      const hasTask = [8, 15, 22, 29].includes(day);
                      return (
                        <motion.div
                          key={i}
                          className={`text-center py-2 rounded-lg text-sm ${
                            !isValid ? 'text-gray-700' :
                            isSelected ? 'bg-emerald-500 text-white font-medium' :
                            hasTask ? 'bg-emerald-500/20 text-emerald-400' :
                            'text-gray-400 hover:bg-gray-800'
                          } ${isValid ? 'cursor-pointer' : ''}`}
                          whileHover={isValid && !isSelected ? { scale: 1.1 } : {}}
                        >
                          {isValid ? day : ''}
                        </motion.div>
                      );
                    })}
                  </div>

                  {/* Time Selection */}
                  <div className="border-t border-gray-800 pt-4 mt-4">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm text-gray-400">Selected: Jan 15, 2025</span>
                      <div className="flex items-center space-x-2 bg-gray-800 rounded-lg px-3 py-1.5">
                        <Clock className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm">09:00 AM</span>
                      </div>
                    </div>

                    {/* Task Preview */}
                    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                          <Mail className="w-4 h-4 text-white" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">Weekly Sales Report</p>
                          <p className="text-xs text-gray-400 mt-1">Repeats every Monday at 9:00 AM</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-900/30">
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

          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "01", title: "Connect Your Tools", desc: "Link Gmail, Drive, Notion, and more with secure OAuth", icon: Wrench },
              { step: "02", title: "Ask in Natural Language", desc: "Simply describe what you want done - no coding needed", icon: MessageSquare },
              { step: "03", title: "Schedule or Run Now", desc: "Execute immediately or schedule for later with recurring options", icon: Calendar },
              { step: "04", title: "Watch It Work", desc: "Our AI executes the task and reports back with results", icon: Zap },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="relative text-center"
              >
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center">
                  <item.icon className="w-7 h-7 text-emerald-400" />
                </div>
                <div className="text-5xl font-bold text-emerald-500/20 mb-2">{item.step}</div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
                {i < 3 && (
                  <ChevronRight className="hidden md:block absolute top-10 -right-3 w-6 h-6 text-gray-700" />
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
      <footer className="border-t border-gray-800 py-16 bg-gray-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Main Footer Content */}
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            {/* Brand Column */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">{APP_METADATA.NAME}</span>
              </div>
              <p className="text-gray-400 text-sm mb-6 max-w-md">
                AI-powered inventory management and workflow automation. Connect your database,
                ask in plain English, and let our AI handle the rest.
              </p>
              {/* Trust Indicators */}
              <div className="flex flex-wrap gap-4">
                <div className="flex items-center space-x-2 text-gray-500 text-xs">
                  <Shield className="w-4 h-4 text-emerald-400" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-500 text-xs">
                  <Lock className="w-4 h-4 text-emerald-400" />
                  <span>256-bit Encryption</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-500 text-xs">
                  <Globe className="w-4 h-4 text-emerald-400" />
                  <span>GDPR Ready</span>
                </div>
              </div>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="font-semibold mb-4 text-white">Product</h4>
              <ul className="space-y-3">
                <li>
                  <a href="#features" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#tools" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Integrations
                  </a>
                </li>
                <li>
                  <a href="#schedule" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Scheduling
                  </a>
                </li>
                <li>
                  <Link href={ROUTES.LOGIN} className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Login
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal Links */}
            <div>
              <h4 className="font-semibold mb-4 text-white">Legal</h4>
              <ul className="space-y-3">
                <li>
                  <a href="#" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Cookie Policy
                  </a>
                </li>
                <li>
                  <a href="mailto:support@storelite.ai" className="text-gray-400 hover:text-emerald-400 text-sm transition-colors">
                    Contact Us
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 text-sm mb-4 md:mb-0">
              © 2025 {APP_METADATA.NAME}. All rights reserved.
            </p>
            {/* Social Proof */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-7 h-7 rounded-full bg-gradient-to-br from-gray-600 to-gray-700 border-2 border-gray-950 flex items-center justify-center"
                    >
                      <Users className="w-3 h-3 text-gray-400" />
                    </div>
                  ))}
                </div>
                <span className="text-gray-400 text-sm">Join 500+ businesses</span>
              </div>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
