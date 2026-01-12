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
MessageCircle, Cpu, Timer, Copy, Check, RotateCcw,
  Plus, ChevronDown
} from 'lucide-react';
import { DemoMarkdown } from '@/components/landing/DemoMarkdown';
import { ThemeToggle } from '@/components/theme-toggle';

// Tool Demo Data with rich markdown responses
const toolDemos = [
  {
    id: 'email',
    name: 'Gmail Integration',
    icon: Mail,
    color: 'from-red-500 to-pink-500',
    bgGlow: 'bg-red-500/20',
    description: 'Send emails, read inbox, and manage communications directly through AI',
    demo: {
      query: "Send sales report to john@company.com",
      response: `**Email Sent Successfully** ✅

**To:** john@company.com
**Subject:** Monthly Sales Report - January 2025
**Attachment:** \`analytics_summary.pdf\`

**Preview:**
> Hi John, Please find attached the monthly sales report with key highlights including 23% revenue growth...

📬 Delivered at 10:32 AM`,
      steps: ['Composing email...', 'Attaching file...', 'Sending...', 'Delivered!']
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
      query: "Find Q4 budget documents",
      response: `**Found 3 documents** 📁

| File | Size | Modified |
|------|------|----------|
| \`Q4_Budget_2024.xlsx\` | 2.4 MB | Dec 15 |
| \`Q4_Proposal.docx\` | 890 KB | Dec 10 |
| \`Q4_Review.pdf\` | 1.2 MB | Dec 20 |

**Quick Summary:**
- Total Budget: **$450,000**
- Spent: $387,500 (86%)
- Status: ✅ Approved`,
      steps: ['Searching Drive...', 'Reading files...', 'Analyzing...', 'Done!']
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
      query: "Create project page for Website Redesign",
      response: `**Page Created** 📝

### Website Redesign Project

**Tasks:**
- [ ] Design mockups (Jan 20)
- [ ] Frontend dev (Feb 5)
- [ ] Backend integration (Feb 15)
- [ ] Testing & QA (Feb 25)
- [x] Project kickoff (Jan 10)

**Team:** @design @engineering
**Status:** 🟢 In Progress

🔗 \`notion.so/website-redesign\``,
      steps: ['Creating page...', 'Adding tasks...', 'Setting up...', 'Created!']
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
      query: "Show 6-month sales trend",
      response: `**Sales Trend Analysis** 📊

\`\`\`
Jul  ████████░░  $82K
Aug  █████████░  $91K  (+11%)
Sep  ███████░░░  $78K  (-14%)
Oct  ██████████  $105K (+35%)
Nov  ██████████▌ $118K (+12%)
Dec  ███████████ $142K (+20%)
\`\`\`

**Insights:**
- 📈 Q4 growth: **+42%**
- 🏆 Best month: December
- 📅 Forecast Jan: **$156K**

💡 Strong holiday season performance`,
      steps: ['Fetching data...', 'Analyzing...', 'Generating chart...', 'Ready!']
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
      query: "Call supplier about order #12345",
      response: `**Call Completed** 📞

**Duration:** 2:34
**Recipient:** ABC Supplies

### Summary:
✅ Order #12345 confirmed
✅ Delivery: **January 18, 2025**
✅ Tracking: \`TRK-789456123\`

**Action Items:**
- Tracking sent to your email
- Invoice ready for download

🎙️ Recording saved`,
      steps: ['Dialing...', 'Connected...', 'Discussing...', 'Complete!']
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

// Animated Cursor Component
function AnimatedCursor({ x, y, clicking }: { x: number; y: number; clicking: boolean }) {
  return (
    <motion.div
      className="absolute z-50 pointer-events-none"
      animate={{ x, y }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
    >
      {/* Cursor SVG */}
      <motion.svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        animate={{ scale: clicking ? 0.85 : 1 }}
        transition={{ duration: 0.1 }}
      >
        <path
          d="M5.5 3.21V20.8c0 .45.54.67.85.35l4.86-4.86a.5.5 0 0 1 .35-.15h6.87c.48 0 .72-.58.38-.92L6.35 2.85a.5.5 0 0 0-.85.36Z"
          fill="#10b981"
          stroke="#ffffff"
          strokeWidth="1.5"
        />
      </motion.svg>
      {/* Click ripple effect */}
      {clicking && (
        <motion.div
          className="absolute top-0 left-0 w-6 h-6 bg-emerald-400/30 rounded-full"
          initial={{ scale: 0.5, opacity: 1 }}
          animate={{ scale: 2, opacity: 0 }}
          transition={{ duration: 0.4 }}
        />
      )}
    </motion.div>
  );
}

// Unified Chat Panel - Single panel with tool selector and auto-tour
function UnifiedChatPanel() {
  const [selectedTool, setSelectedTool] = useState<typeof toolDemos[0] | null>(null);
  const [showToolSelector, setShowToolSelector] = useState(false);
  const [demoState, setDemoState] = useState<'idle' | 'typing_in_input' | 'sent' | 'thinking' | 'streaming' | 'complete'>('idle');
  const [inputText, setInputText] = useState('');
  const [streamedResponse, setStreamedResponse] = useState('');
  const [currentStep, setCurrentStep] = useState(0);
  const [copied, setCopied] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  // Auto-tour state - always active, non-stoppable
  const [currentToolIndex, setCurrentToolIndex] = useState(0);
  const [cursorPos, setCursorPos] = useState({ x: 200, y: 200 });
  const [cursorClicking, setCursorClicking] = useState(false);
  const [tourPhase, setTourPhase] = useState<'idle' | 'move_to_dropdown' | 'open_dropdown' | 'move_to_tool' | 'select_tool' | 'demo_running' | 'pause'>('idle');
  const toolsButtonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [inputText, streamedResponse, demoState]);

  // Select tool and start demo
  const selectTool = (tool: typeof toolDemos[0]) => {
    setSelectedTool(tool);
    setShowToolSelector(false);
    setDemoState('idle');
    setInputText('');
    setStreamedResponse('');
    setCurrentStep(0);
    setCopied(false);
    // Auto-start demo after selection
    setTimeout(() => startDemo(tool), 300);
  };

  // Start demo
  const startDemo = (tool: typeof toolDemos[0]) => {
    setDemoState('typing_in_input');
    setInputText('');
    setStreamedResponse('');
    setCurrentStep(0);
    setCopied(false);
  };

  // Reset to tool selection
  const resetToSelection = () => {
    setSelectedTool(null);
    setDemoState('idle');
    setInputText('');
    setStreamedResponse('');
    setCurrentStep(0);
  };

  // Copy response
  const copyResponse = async () => {
    if (!selectedTool) return;
    await navigator.clipboard.writeText(selectedTool.demo.response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Auto-tour is always active - no stopping
  // Removed user interaction stop

  // Auto-tour controller - manages the automated demo sequence (always active)
  useEffect(() => {
    if (!isInView) return;

    let timeout: NodeJS.Timeout;

    // Start tour when component becomes visible
    if (tourPhase === 'idle' && !selectedTool) {
      timeout = setTimeout(() => {
        setTourPhase('move_to_dropdown');
        // Move cursor to Tools button area
        setCursorPos({ x: 620, y: 35 });
      }, 1500);
    }

    // Open dropdown
    else if (tourPhase === 'move_to_dropdown') {
      timeout = setTimeout(() => {
        setCursorClicking(true);
        setTimeout(() => {
          setCursorClicking(false);
          setShowToolSelector(true);
          setTourPhase('move_to_tool');
          // Move cursor to first tool in dropdown
          const toolY = 95 + (currentToolIndex * 52);
          setCursorPos({ x: 550, y: toolY });
        }, 150);
      }, 800);
    }

    // Select tool
    else if (tourPhase === 'move_to_tool') {
      timeout = setTimeout(() => {
        setCursorClicking(true);
        setTimeout(() => {
          setCursorClicking(false);
          // Select the tool
          const tool = toolDemos[currentToolIndex];
          setSelectedTool(tool);
          setShowToolSelector(false);
          setTourPhase('demo_running');
          // Start demo
          setDemoState('typing_in_input');
          setInputText('');
          setStreamedResponse('');
          setCurrentStep(0);
          // Move cursor to input area
          setCursorPos({ x: 350, y: 450 });
        }, 150);
      }, 600);
    }

    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [isInView, tourPhase, currentToolIndex, selectedTool]);

  // Watch for demo completion to move to next tool
  useEffect(() => {

    if (demoState === 'complete' && tourPhase === 'demo_running') {
      // Wait 4 seconds then move to next tool
      const timeout = setTimeout(() => {
        setTourPhase('pause');
        // Reset for next tool
        setSelectedTool(null);
        setDemoState('idle');
        setInputText('');
        setStreamedResponse('');

        // Move to next tool (loop back to 0 after last)
        const nextIndex = (currentToolIndex + 1) % toolDemos.length;
        setCurrentToolIndex(nextIndex);

        // Small pause then restart
        setTimeout(() => {
          setCursorPos({ x: 200, y: 200 });
          setTourPhase('move_to_dropdown');
          setCursorPos({ x: 620, y: 35 });
        }, 500);
      }, 4000);

      return () => clearTimeout(timeout);
    }
  }, [demoState, tourPhase, currentToolIndex]);

  // Phase 1: Typing
  useEffect(() => {
    if (demoState !== 'typing_in_input' || !selectedTool) return;

    const query = selectedTool.demo.query;
    let i = 0;
    const interval = setInterval(() => {
      if (i < query.length) {
        setInputText(query.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          setDemoState('sent');
          setTimeout(() => setDemoState('thinking'), 300);
        }, 500);
      }
    }, 30);

    return () => clearInterval(interval);
  }, [demoState, selectedTool]);

  // Phase 2: Thinking
  useEffect(() => {
    if (demoState !== 'thinking' || !selectedTool) return;

    const steps = selectedTool.demo.steps;
    let stepIdx = 0;
    setCurrentStep(0);

    const stepInterval = setInterval(() => {
      stepIdx++;
      if (stepIdx < steps.length) {
        setCurrentStep(stepIdx);
      } else {
        clearInterval(stepInterval);
        setTimeout(() => setDemoState('streaming'), 400);
      }
    }, 600);

    return () => clearInterval(stepInterval);
  }, [demoState, selectedTool]);

  // Phase 3: Streaming
  useEffect(() => {
    if (demoState !== 'streaming' || !selectedTool) return;

    const response = selectedTool.demo.response;
    let i = 0;
    const interval = setInterval(() => {
      if (i < response.length) {
        setStreamedResponse(response.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
        setDemoState('complete');
      }
    }, 8);

    return () => clearInterval(interval);
  }, [demoState, selectedTool]);

  const showMessageInChat = demoState === 'sent' || demoState === 'thinking' || demoState === 'streaming' || demoState === 'complete';

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className="max-w-4xl mx-auto"
    >
      {/* Glow Effect */}
      <div className="relative" ref={panelRef}>
        <div className="absolute -inset-2 bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-blue-500/20 rounded-3xl blur-2xl" />

        <div className="relative bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          {/* Animated Cursor for auto-tour - always visible when in view */}
          {isInView && (
            <AnimatedCursor x={cursorPos.x} y={cursorPos.y} clicking={cursorClicking} />
          )}
          {/* Header with Tool Selector */}
          <div className="bg-gray-900/90 backdrop-blur-sm border-b border-gray-800 px-4 py-3">
            <div className="flex items-center justify-between">
              {/* Left: Tool selector or brand */}
              <div className="flex items-center space-x-3">
                {selectedTool ? (
                  <>
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${selectedTool.color} flex items-center justify-center shadow-lg`}>
                      <selectedTool.icon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">{selectedTool.name}</h3>
                      <p className="text-xs text-gray-500">AI-powered integration</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">AI Agent</h3>
                      <p className="text-xs text-gray-500">Select a tool to see demo</p>
                    </div>
                  </>
                )}
              </div>

              {/* Right: Actions */}
              <div className="flex items-center space-x-2">
                {/* Tool Selector Dropdown */}
                <div className="relative">
                  <button
                    ref={toolsButtonRef}
                    className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-xl px-3 py-2 transition-colors pointer-events-none"
                  >
                    <Plus className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-300">Tools</span>
                    <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showToolSelector ? 'rotate-180' : ''}`} />
                  </button>

                  {/* Dropdown Menu */}
                  <AnimatePresence>
                    {showToolSelector && (
                      <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 top-full mt-2 w-64 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-50 overflow-hidden"
                      >
                        <div className="p-2">
                          <p className="text-xs text-gray-500 px-2 py-1 mb-1">Select a tool to demo</p>
                          {toolDemos.map((tool) => (
                            <div
                              key={tool.id}
                              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors pointer-events-none ${
                                selectedTool?.id === tool.id
                                  ? 'bg-emerald-500/20 border border-emerald-500/30'
                                  : 'hover:bg-gray-700/50'
                              }`}
                            >
                              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${tool.color} flex items-center justify-center`}>
                                <tool.icon className="w-4 h-4 text-white" />
                              </div>
                              <div className="text-left flex-1">
                                <p className="text-sm font-medium text-white">{tool.name}</p>
                                <p className="text-xs text-gray-500 truncate">{tool.description.slice(0, 35)}...</p>
                              </div>
                              {selectedTool?.id === tool.id && (
                                <Check className="w-4 h-4 text-emerald-400" />
                              )}
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Online Status */}
                <div className="flex items-center space-x-1.5 bg-emerald-500/10 px-2.5 py-1.5 rounded-full">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-[10px] text-emerald-400 font-medium">ONLINE</span>
                </div>

                {/* Reset Button */}
                {selectedTool && demoState === 'complete' && (
                  <button
                    onClick={resetToSelection}
                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                    title="Try another tool"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Chat Area */}
          <div
            ref={chatRef}
            className="h-[380px] overflow-y-auto p-6 space-y-4 bg-[#0a0a0f]"
            style={{
              backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.04) 0%, transparent 50%)'
            }}
          >
            {/* Initial state - no tool selected */}
            {!selectedTool && (
              <div className="h-full flex flex-col items-center justify-center text-center px-4">
                <motion.div
                  className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center mb-5 shadow-lg"
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Sparkles className="w-8 h-8 text-white" />
                </motion.div>
                <h4 className="text-white font-semibold text-lg mb-2">Try Our Integrations</h4>
                <p className="text-gray-500 text-sm mb-6 max-w-sm leading-relaxed">
                  Select a tool from the dropdown above or click one below to see how our AI agent works with your favorite services.
                </p>

                {/* Quick Tool Select Grid - Display only */}
                <div className="flex flex-wrap justify-center gap-2 pointer-events-none">
                  {toolDemos.map((tool) => (
                    <div
                      key={tool.id}
                      className={`flex items-center space-x-2 px-4 py-2 bg-gray-800/80 border border-gray-700/50 rounded-xl`}
                    >
                      <div className={`w-6 h-6 rounded-lg bg-gradient-to-br ${tool.color} flex items-center justify-center`}>
                        <tool.icon className="w-3.5 h-3.5 text-white" />
                      </div>
                      <span className="text-sm text-gray-300">{tool.name.split(' ')[0]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tool selected - show demo */}
            {selectedTool && (
              <>
                {/* User Message */}
                {showMessageInChat && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className="flex justify-end"
                  >
                    <div className="max-w-[80%]">
                      <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-br-md px-4 py-3 text-sm shadow-lg shadow-blue-600/20">
                        {selectedTool.demo.query}
                      </div>
                      <div className="text-[10px] text-gray-600 text-right mt-1.5 mr-1">Just now</div>
                    </div>
                  </motion.div>
                )}

                {/* Thinking indicator */}
                {demoState === 'thinking' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-start space-x-3"
                  >
                    <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${selectedTool.color} flex items-center justify-center flex-shrink-0 shadow-lg`}>
                      <Bot className="w-4.5 h-4.5 text-white" />
                    </div>
                    <div className="bg-gray-800/90 backdrop-blur-sm rounded-2xl rounded-bl-md px-4 py-3 border border-gray-700/50">
                      <div className="flex items-center space-x-3">
                        <div className="flex space-x-1">
                          {[0, 1, 2].map(i => (
                            <motion.span
                              key={i}
                              className={`w-2 h-2 rounded-full bg-gradient-to-r ${selectedTool.color}`}
                              animate={{
                                scale: [1, 1.4, 1],
                                opacity: [0.4, 1, 0.4]
                              }}
                              transition={{
                                duration: 0.8,
                                repeat: Infinity,
                                delay: i * 0.15
                              }}
                            />
                          ))}
                        </div>
                        <span className="text-xs text-gray-400 font-medium">
                          {selectedTool.demo.steps[currentStep]}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* AI Response */}
                {(demoState === 'streaming' || demoState === 'complete') && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-start space-x-3"
                  >
                    <div className={`w-9 h-9 rounded-full bg-gradient-to-br ${selectedTool.color} flex items-center justify-center flex-shrink-0 shadow-lg`}>
                      <Bot className="w-4.5 h-4.5 text-white" />
                    </div>
                    <div className="flex-1 max-w-[85%]">
                      <div className="bg-gray-800/90 backdrop-blur-sm rounded-2xl rounded-bl-md px-4 py-3 border border-gray-700/50">
                        <DemoMarkdown
                          content={streamedResponse}
                          isStreaming={demoState === 'streaming'}
                        />
                      </div>

                      {/* Message actions */}
                      {demoState === 'complete' && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.3 }}
                          className="flex items-center space-x-3 mt-2 ml-1"
                        >
                          <button
                            onClick={copyResponse}
                            className="flex items-center space-x-1 text-[10px] text-gray-500 hover:text-gray-300 transition-colors px-2 py-1 rounded-md hover:bg-gray-800/50"
                          >
                            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            <span>{copied ? 'Copied!' : 'Copy'}</span>
                          </button>
                          <span className="text-gray-700">•</span>
                          <span className="text-[10px] text-gray-600">Just now</span>
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                )}
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-800 p-4 bg-gray-900/90 backdrop-blur-sm">
            <div className="flex items-center space-x-3">
              {/* Tool quick-select in input */}
              {selectedTool && (
                <div className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-gradient-to-r ${selectedTool.color} bg-opacity-20 border border-gray-700/50`}>
                  <selectedTool.icon className="w-3.5 h-3.5 text-white/80" />
                  <span className="text-xs text-white/80 font-medium">{selectedTool.name.split(' ')[0]}</span>
                </div>
              )}

              <div className="flex-1 bg-gray-800/80 rounded-xl px-4 py-3 min-h-[48px] flex items-center border border-gray-700/50">
                {demoState === 'typing_in_input' && selectedTool ? (
                  <span className="text-white text-sm">
                    {inputText}
                    <motion.span
                      className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 align-middle rounded-full"
                      animate={{ opacity: [1, 0, 1] }}
                      transition={{ duration: 0.5, repeat: Infinity }}
                    />
                  </span>
                ) : (
                  <span className="text-gray-500 text-sm">
                    {selectedTool ? 'Ask anything...' : 'Select a tool to start...'}
                  </span>
                )}
              </div>

              <motion.button
                className={`p-3 rounded-xl transition-all ${
                  demoState === 'typing_in_input' && inputText.length > 0
                    ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white shadow-lg'
                    : 'bg-gray-800 text-gray-500 border border-gray-700/50'
                }`}
                animate={demoState === 'typing_in_input' && inputText.length > 0 ? { scale: [1, 1.05, 1] } : {}}
              >
                <Send className="w-5 h-5" />
              </motion.button>
            </div>

            {/* Try another tool */}
            {demoState === 'complete' && selectedTool && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-center mt-4"
              >
                <button
                  onClick={resetToSelection}
                  className="flex items-center space-x-2 text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 rounded-xl hover:bg-gray-800/50"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Try Another Tool</span>
                </button>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* Tool chips below panel - Shows current tool highlighted */}
      <div className="flex flex-wrap justify-center gap-2 mt-6">
        {toolDemos.map((tool) => (
          <div
            key={tool.id}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
              selectedTool?.id === tool.id
                ? `bg-gradient-to-r ${tool.color} text-white shadow-lg`
                : 'bg-gray-800/60 text-gray-400 border border-gray-700/50'
            }`}
          >
            <tool.icon className="w-3.5 h-3.5" />
            <span>{tool.name.split(' ')[0]}</span>
          </div>
        ))}
      </div>

      {/* Auto-tour indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex justify-center mt-4"
      >
        <div className="flex items-center space-x-2 text-xs text-gray-500 bg-gray-800/50 px-3 py-1.5 rounded-full">
          <motion.div
            className="w-2 h-2 bg-emerald-400 rounded-full"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <span>Live demo • Cycling through all integrations</span>
        </div>
      </motion.div>
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
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-white overflow-x-hidden transition-colors">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800/50 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">{APP_METADATA.NAME}</span>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium">
              Features
            </a>
            <a href="#tools" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium">
              Integrations
            </a>
            <a href="#schedule" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-sm font-medium">
              Schedule Tasks
            </a>
          </nav>

          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <Link
              href={ROUTES.LOGIN}
              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors font-medium"
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
            {/* Compact Headline */}
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold mb-2 text-gray-700 dark:text-gray-200">
              Your Database.{' '}
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent font-bold">
                Now Intelligent.
              </span>
            </h1>

            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-500 mb-8 max-w-xl mx-auto">
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
              {/* Feature Badges with Icons & Links */}
              <div className="flex flex-wrap justify-center gap-3 mb-8">
                <a
                  href="#features"
                  className="group flex items-center space-x-2 bg-gray-100 dark:bg-gray-800/60 hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700/50 hover:border-emerald-500/50 rounded-full px-4 py-2 transition-all"
                >
                  <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <Database className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">Automate inventory queries</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500 group-hover:text-emerald-500 dark:group-hover:text-emerald-400 transition-colors" />
                </a>
                <a
                  href="#tools"
                  className="group flex items-center space-x-2 bg-gray-100 dark:bg-gray-800/60 hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700/50 hover:border-cyan-500/50 rounded-full px-4 py-2 transition-all"
                >
                  <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <BarChart3 className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">Generate reports instantly</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500 group-hover:text-cyan-500 dark:group-hover:text-cyan-400 transition-colors" />
                </a>
                <a
                  href="#schedule"
                  className="group flex items-center space-x-2 bg-gray-100 dark:bg-gray-800/60 hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700/50 hover:border-purple-500/50 rounded-full px-4 py-2 transition-all"
                >
                  <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Calendar className="w-3.5 h-3.5 text-purple-500 dark:text-purple-400" />
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">Schedule recurring tasks</span>
                  <ChevronRight className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500 group-hover:text-purple-500 dark:group-hover:text-purple-400 transition-colors" />
                </a>
              </div>

              {/* Primary & Secondary CTAs */}
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
                <a
                  href="mailto:demo@storelite.ai?subject=Schedule%20a%20Demo"
                  className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 px-6 py-3 rounded-xl transition-all"
                >
                  <Play className="w-4 h-4" />
                  <span className="font-medium">Schedule a Demo</span>
                </a>
              </div>

              {/* Trust Indicators */}
              <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-500 text-sm mt-4">
                <Lock className="w-4 h-4" />
                <span>256-bit encryption • SOC 2 compliant</span>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-gray-200 dark:border-gray-800">
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
              <div className="text-gray-600 dark:text-gray-400 mt-2">Integrated Tools</div>
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
              <div className="text-gray-600 dark:text-gray-400 mt-2">Uptime Guaranteed</div>
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
              <div className="text-gray-600 dark:text-gray-400 mt-2">Support Available</div>
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
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
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
                className="bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-6 hover:border-emerald-500/50 transition-colors group"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center mb-4 group-hover:from-emerald-500/30 group-hover:to-cyan-500/30 transition-colors">
                  <feature.icon className="w-6 h-6 text-emerald-500 dark:text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tool Demos Section - Unified Chat Panel */}
      <section id="tools" className="py-20 bg-gray-50 dark:bg-gray-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Powerful <span className="text-emerald-400">Integrations</span>
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              One AI agent, multiple tools. Select any integration below to see how our agent
              automates tasks across Gmail, Drive, Notion, and more.
            </p>
          </motion.div>

          {/* Unified Chat Panel */}
          <UnifiedChatPanel />
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
              <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
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
                  <span className="text-sm text-gray-400">January 2026</span>
                </div>

                {/* Mock Calendar Grid - January 2026 starts on Thursday (offset 4) */}
                <div className="p-6">
                  <div className="grid grid-cols-7 gap-2 mb-4">
                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                      <div key={i} className="text-center text-xs text-gray-500 font-medium py-2">
                        {day}
                      </div>
                    ))}
                    {Array.from({ length: 35 }, (_, i) => {
                      const day = i - 3; // January 2026 starts on Thursday (index 4, so offset is 3)
                      const isValid = day >= 1 && day <= 31;
                      const isSelected = day === 15;
                      const hasTask = [5, 12, 19, 26].includes(day); // Mondays in Jan 2026
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
                      <span className="text-sm text-gray-400">Selected: Jan 15, 2026</span>
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
              <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
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
            <div className="relative bg-gray-100 dark:bg-gray-900/80 border border-gray-200 dark:border-gray-800 rounded-2xl p-12">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Ready to Automate Your Workflow?
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
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
      <footer className="border-t border-gray-200 dark:border-gray-800 py-16 bg-gray-50 dark:bg-gray-950">
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
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-6 max-w-md">
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
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-3">
                <li>
                  <a href="#features" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#tools" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Integrations
                  </a>
                </li>
                <li>
                  <a href="#schedule" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Scheduling
                  </a>
                </li>
                <li>
                  <Link href={ROUTES.LOGIN} className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Login
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal Links */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-3">
                <li>
                  <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Cookie Policy
                  </a>
                </li>
                <li>
                  <a href="mailto:support@storelite.ai" className="text-gray-600 dark:text-gray-400 hover:text-emerald-500 dark:hover:text-emerald-400 text-sm transition-colors">
                    Contact Us
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-200 dark:border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 dark:text-gray-500 text-sm mb-4 md:mb-0">
              © 2025 {APP_METADATA.NAME}. All rights reserved.
            </p>
            {/* Social Proof */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-7 h-7 rounded-full bg-gradient-to-br from-gray-300 dark:from-gray-600 to-gray-400 dark:to-gray-700 border-2 border-white dark:border-gray-950 flex items-center justify-center"
                    >
                      <Users className="w-3 h-3 text-gray-500 dark:text-gray-400" />
                    </div>
                  ))}
                </div>
                <span className="text-gray-600 dark:text-gray-400 text-sm">Join 500+ businesses</span>
              </div>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
