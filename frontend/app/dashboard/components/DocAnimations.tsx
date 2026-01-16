/**
 * Documentation Animated Illustrations
 *
 * Animated components that demonstrate app features in the documentation.
 * Uses Framer Motion with the same patterns as the landing page.
 *
 * Color scheme: Emerald (#10b981) + Cyan (#06b6d4) gradients
 * Animation style: Smooth spring physics, scroll-triggered reveals
 *
 * v1.0: Initial implementation with Dashboard, AI Agent, Scheduler, Tools, and Shortcuts demos
 */

'use client';

import { motion, AnimatePresence, Variants } from 'framer-motion';
import { useState, useEffect } from 'react';
import {
  Package, TrendingUp, CheckCircle, AlertCircle, Bot,
  Send, Sparkles, Calendar, Clock, Zap, Database,
  Mail, FileText, Settings, Command, ArrowRight,
  BarChart3, Users, ShoppingCart, Bell, Search
} from 'lucide-react';

// ============================================================================
// Animation Variants (Reusable)
// ============================================================================

const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 }
  }
};

const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring', stiffness: 200, damping: 20 }
  }
};

const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4 }
  }
};

const slideInRight: Variants = {
  hidden: { opacity: 0, x: 30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4 }
  }
};

// ============================================================================
// Dashboard Demo Animation
// ============================================================================

export function DashboardDemo() {
  const [activeKpi, setActiveKpi] = useState(0);
  const [checklistProgress, setChecklistProgress] = useState(0);

  useEffect(() => {
    // Cycle through KPIs
    const kpiInterval = setInterval(() => {
      setActiveKpi((prev) => (prev + 1) % 4);
    }, 2000);

    // Animate checklist progress
    const progressInterval = setInterval(() => {
      setChecklistProgress((prev) => (prev >= 100 ? 0 : prev + 25));
    }, 1500);

    return () => {
      clearInterval(kpiInterval);
      clearInterval(progressInterval);
    };
  }, []);

  const kpis = [
    { icon: Package, label: 'Total Items', value: '1,234', color: 'emerald', trend: '+12%' },
    { icon: TrendingUp, label: 'Revenue', value: '$45.2K', color: 'cyan', trend: '+8%' },
    { icon: ShoppingCart, label: 'Orders', value: '89', color: 'violet', trend: '+15%' },
    { icon: Users, label: 'Customers', value: '456', color: 'amber', trend: '+5%' },
  ];

  const checklistItems = [
    { label: 'Review low stock items', done: checklistProgress >= 25 },
    { label: 'Process pending orders', done: checklistProgress >= 50 },
    { label: 'Update inventory counts', done: checklistProgress >= 75 },
    { label: 'Generate daily report', done: checklistProgress >= 100 },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Animated background gradient */}
      <motion.div
        className="absolute inset-0 opacity-30"
        animate={{
          background: [
            'radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.3) 0%, transparent 50%)',
            'radial-gradient(circle at 80% 50%, rgba(6, 182, 212, 0.3) 0%, transparent 50%)',
            'radial-gradient(circle at 50% 80%, rgba(16, 185, 129, 0.3) 0%, transparent 50%)',
            'radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.3) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
      />

      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center justify-between mb-4"
      >
        <div className="flex items-center gap-2">
          <motion.div
            className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
          >
            <BarChart3 className="w-4 h-4 text-white" />
          </motion.div>
          <span className="text-white font-semibold text-sm">Dashboard</span>
        </div>
        <motion.div
          className="flex items-center gap-2"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Bell className="w-4 h-4 text-gray-400" />
          <div className="w-2 h-2 bg-emerald-500 rounded-full" />
        </motion.div>
      </motion.div>

      {/* KPI Cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-2 gap-2 mb-4"
      >
        {kpis.map((kpi, index) => (
          <motion.div
            key={kpi.label}
            variants={scaleIn}
            className={`
              relative p-3 rounded-lg border transition-all duration-300
              ${activeKpi === index
                ? 'bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border-emerald-500/50'
                : 'bg-gray-800/50 border-gray-700/50'
              }
            `}
            whileHover={{ scale: 1.02 }}
          >
            <motion.div
              animate={activeKpi === index ? { scale: [1, 1.1, 1] } : {}}
              transition={{ duration: 0.5 }}
            >
              <kpi.icon className={`w-4 h-4 mb-1 ${
                activeKpi === index ? 'text-emerald-400' : 'text-gray-500'
              }`} />
            </motion.div>
            <p className="text-[10px] text-gray-400">{kpi.label}</p>
            <p className="text-sm font-bold text-white">{kpi.value}</p>
            <span className={`text-[10px] ${
              kpi.trend.startsWith('+') ? 'text-emerald-400' : 'text-red-400'
            }`}>
              {kpi.trend}
            </span>
          </motion.div>
        ))}
      </motion.div>

      {/* Checklist */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Today&apos;s Tasks</span>
          <span className="text-xs text-emerald-400">{checklistProgress}%</span>
        </div>
        <div className="space-y-1.5">
          {checklistItems.map((item, index) => (
            <motion.div
              key={item.label}
              className="flex items-center gap-2"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <motion.div
                animate={item.done ? { scale: [1, 1.2, 1] } : {}}
                transition={{ duration: 0.3 }}
              >
                {item.done ? (
                  <CheckCircle className="w-3 h-3 text-emerald-400" />
                ) : (
                  <div className="w-3 h-3 rounded-full border border-gray-600" />
                )}
              </motion.div>
              <span className={`text-[10px] ${item.done ? 'text-gray-400 line-through' : 'text-gray-300'}`}>
                {item.label}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// ============================================================================
// AI Agent Chat Demo Animation
// ============================================================================

export function AIAgentDemo() {
  const [stage, setStage] = useState<'idle' | 'typing' | 'thinking' | 'response'>('idle');
  const [showResponse, setShowResponse] = useState(false);

  useEffect(() => {
    const cycle = async () => {
      // Reset
      setStage('idle');
      setShowResponse(false);
      await new Promise(r => setTimeout(r, 1000));

      // User typing
      setStage('typing');
      await new Promise(r => setTimeout(r, 1500));

      // Agent thinking
      setStage('thinking');
      await new Promise(r => setTimeout(r, 2000));

      // Response
      setStage('response');
      setShowResponse(true);
      await new Promise(r => setTimeout(r, 3000));
    };

    cycle();
    const interval = setInterval(cycle, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Animated background */}
      <motion.div
        className="absolute inset-0 opacity-20"
        animate={{
          background: [
            'radial-gradient(circle at 30% 30%, rgba(16, 185, 129, 0.4) 0%, transparent 40%)',
            'radial-gradient(circle at 70% 70%, rgba(6, 182, 212, 0.4) 0%, transparent 40%)',
          ],
        }}
        transition={{ duration: 4, repeat: Infinity, repeatType: 'reverse' }}
      />

      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{
            boxShadow: stage === 'thinking'
              ? ['0 0 0 0 rgba(16, 185, 129, 0)', '0 0 20px 10px rgba(16, 185, 129, 0.3)', '0 0 0 0 rgba(16, 185, 129, 0)']
              : '0 0 0 0 rgba(16, 185, 129, 0)'
          }}
          transition={{ duration: 1, repeat: stage === 'thinking' ? Infinity : 0 }}
        >
          <Bot className="w-4 h-4 text-white" />
        </motion.div>
        <div>
          <span className="text-white font-semibold text-sm">AI Assistant</span>
          <motion.p
            className="text-[10px] text-emerald-400"
            animate={{ opacity: stage === 'thinking' ? [0.5, 1, 0.5] : 1 }}
            transition={{ duration: 0.5, repeat: stage === 'thinking' ? Infinity : 0 }}
          >
            {stage === 'thinking' ? 'Analyzing...' : 'Online'}
          </motion.p>
        </div>
      </motion.div>

      {/* Chat Messages */}
      <div className="space-y-3 mb-4">
        {/* User Message */}
        <AnimatePresence>
          {(stage === 'typing' || stage === 'thinking' || stage === 'response') && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-end"
            >
              <div className="bg-emerald-600/30 border border-emerald-500/30 rounded-lg px-3 py-2 max-w-[80%]">
                <p className="text-xs text-white">Show me items with low stock</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Thinking Animation */}
        <AnimatePresence>
          {stage === 'thinking' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-start gap-2"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-3 h-3 text-white" />
              </div>
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg px-3 py-2">
                <motion.div className="flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-1.5 h-1.5 bg-emerald-400 rounded-full"
                      animate={{ y: [0, -4, 0] }}
                      transition={{ duration: 0.5, repeat: Infinity, delay: i * 0.15 }}
                    />
                  ))}
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* AI Response */}
        <AnimatePresence>
          {showResponse && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-start gap-2"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
                <Bot className="w-3 h-3 text-white" />
              </div>
              <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg px-3 py-2 flex-1">
                <p className="text-xs text-gray-300 mb-2">Found 3 items with low stock:</p>
                <motion.div
                  className="space-y-1"
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                >
                  {[
                    { name: 'Widget A', stock: 5, threshold: 10 },
                    { name: 'Gadget B', stock: 3, threshold: 15 },
                    { name: 'Part C', stock: 8, threshold: 20 },
                  ].map((item, i) => (
                    <motion.div
                      key={item.name}
                      variants={slideInLeft}
                      className="flex items-center justify-between bg-gray-700/30 rounded px-2 py-1"
                    >
                      <span className="text-[10px] text-white">{item.name}</span>
                      <span className="text-[10px] text-amber-400">{item.stock}/{item.threshold}</span>
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <motion.div
        className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2 border border-gray-700/50"
        animate={{
          borderColor: stage === 'typing' ? 'rgba(16, 185, 129, 0.5)' : 'rgba(55, 65, 81, 0.5)'
        }}
      >
        <Search className="w-3 h-3 text-gray-500" />
        <motion.span
          className="text-[10px] text-gray-500 flex-1"
          animate={{ opacity: stage === 'idle' ? [0.5, 1, 0.5] : 1 }}
          transition={{ duration: 1.5, repeat: stage === 'idle' ? Infinity : 0 }}
        >
          {stage === 'typing' ? 'Show me items with low stock|' : 'Ask anything about your inventory...'}
        </motion.span>
        <motion.div
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <Send className="w-3 h-3 text-emerald-400" />
        </motion.div>
      </motion.div>
    </div>
  );
}

// ============================================================================
// Scheduler Demo Animation
// ============================================================================

export function SchedulerDemo() {
  const [activeTask, setActiveTask] = useState(0);
  const [showNewTask, setShowNewTask] = useState(false);

  useEffect(() => {
    const taskInterval = setInterval(() => {
      setActiveTask((prev) => (prev + 1) % 3);
    }, 2500);

    const newTaskInterval = setInterval(() => {
      setShowNewTask(true);
      setTimeout(() => setShowNewTask(false), 2000);
    }, 5000);

    return () => {
      clearInterval(taskInterval);
      clearInterval(newTaskInterval);
    };
  }, []);

  const tasks = [
    { name: 'Daily Report', time: '09:00 AM', icon: FileText, status: 'completed' },
    { name: 'Stock Check', time: '12:00 PM', icon: Package, status: 'running' },
    { name: 'Email Summary', time: '05:00 PM', icon: Mail, status: 'pending' },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Background animation */}
      <motion.div
        className="absolute inset-0 opacity-20"
        animate={{
          background: [
            'linear-gradient(45deg, rgba(16, 185, 129, 0.2) 0%, transparent 50%)',
            'linear-gradient(225deg, rgba(6, 182, 212, 0.2) 0%, transparent 50%)',
          ],
        }}
        transition={{ duration: 5, repeat: Infinity, repeatType: 'reverse' }}
      />

      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center justify-between mb-4"
      >
        <div className="flex items-center gap-2">
          <motion.div
            className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          >
            <Calendar className="w-4 h-4 text-white" />
          </motion.div>
          <span className="text-white font-semibold text-sm">Task Scheduler</span>
        </div>
        <motion.button
          className="px-2 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded text-[10px] text-emerald-400"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          + New Task
        </motion.button>
      </motion.div>

      {/* Task List */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {tasks.map((task, index) => (
          <motion.div
            key={task.name}
            variants={scaleIn}
            className={`
              relative flex items-center gap-3 p-3 rounded-lg border transition-all
              ${activeTask === index
                ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border-emerald-500/50'
                : 'bg-gray-800/50 border-gray-700/50'
              }
            `}
            whileHover={{ x: 4 }}
          >
            <motion.div
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                task.status === 'completed' ? 'bg-emerald-500/20' :
                task.status === 'running' ? 'bg-cyan-500/20' : 'bg-gray-700/50'
              }`}
              animate={task.status === 'running' && activeTask === index ? {
                boxShadow: ['0 0 0 0 rgba(6, 182, 212, 0)', '0 0 10px 5px rgba(6, 182, 212, 0.3)', '0 0 0 0 rgba(6, 182, 212, 0)']
              } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <task.icon className={`w-4 h-4 ${
                task.status === 'completed' ? 'text-emerald-400' :
                task.status === 'running' ? 'text-cyan-400' : 'text-gray-500'
              }`} />
            </motion.div>
            <div className="flex-1">
              <p className="text-xs text-white font-medium">{task.name}</p>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-gray-500" />
                <span className="text-[10px] text-gray-500">{task.time}</span>
              </div>
            </div>
            <div className={`px-2 py-0.5 rounded text-[10px] ${
              task.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
              task.status === 'running' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-gray-700 text-gray-400'
            }`}>
              {task.status}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* New Task Animation */}
      <AnimatePresence>
        {showNewTask && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.9 }}
            className="absolute inset-x-4 bottom-4 bg-emerald-500/20 border border-emerald-500/50 rounded-lg p-3 backdrop-blur-sm"
          >
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-emerald-400">New task created successfully!</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// Connected Tools Demo Animation
// ============================================================================

export function ConnectedToolsDemo() {
  const [activeConnection, setActiveConnection] = useState(0);
  const [dataFlow, setDataFlow] = useState(false);

  useEffect(() => {
    const connectionInterval = setInterval(() => {
      setActiveConnection((prev) => (prev + 1) % 4);
    }, 2000);

    const flowInterval = setInterval(() => {
      setDataFlow(true);
      setTimeout(() => setDataFlow(false), 1500);
    }, 3000);

    return () => {
      clearInterval(connectionInterval);
      clearInterval(flowInterval);
    };
  }, []);

  const tools = [
    { name: 'Database', icon: Database, color: 'emerald', connected: true },
    { name: 'Email', icon: Mail, color: 'cyan', connected: true },
    { name: 'Files', icon: FileText, color: 'violet', connected: true },
    { name: 'API', icon: Zap, color: 'amber', connected: false },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Animated lines background */}
      <svg className="absolute inset-0 w-full h-full opacity-20">
        <motion.line
          x1="50%"
          y1="30%"
          x2="20%"
          y2="60%"
          stroke="url(#lineGradient)"
          strokeWidth="2"
          animate={{ opacity: dataFlow ? [0.3, 1, 0.3] : 0.3 }}
          transition={{ duration: 1, repeat: dataFlow ? Infinity : 0 }}
        />
        <motion.line
          x1="50%"
          y1="30%"
          x2="80%"
          y2="60%"
          stroke="url(#lineGradient)"
          strokeWidth="2"
          animate={{ opacity: dataFlow ? [0.3, 1, 0.3] : 0.3 }}
          transition={{ duration: 1, repeat: dataFlow ? Infinity : 0, delay: 0.2 }}
        />
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>

      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{ scale: dataFlow ? [1, 1.1, 1] : 1 }}
          transition={{ duration: 0.5 }}
        >
          <Settings className="w-4 h-4 text-white" />
        </motion.div>
        <span className="text-white font-semibold text-sm">Connected Tools</span>
      </motion.div>

      {/* Central Hub */}
      <div className="relative flex justify-center mb-4">
        <motion.div
          className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{
            boxShadow: dataFlow
              ? ['0 0 0 0 rgba(16, 185, 129, 0)', '0 0 30px 15px rgba(16, 185, 129, 0.3)', '0 0 0 0 rgba(16, 185, 129, 0)']
              : '0 0 0 0 rgba(16, 185, 129, 0)'
          }}
          transition={{ duration: 1.5, repeat: dataFlow ? Infinity : 0 }}
        >
          <Bot className="w-8 h-8 text-white" />
        </motion.div>
      </div>

      {/* Tools Grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-2 gap-2"
      >
        {tools.map((tool, index) => (
          <motion.div
            key={tool.name}
            variants={scaleIn}
            className={`
              relative flex items-center gap-2 p-2 rounded-lg border transition-all
              ${activeConnection === index
                ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border-emerald-500/50'
                : 'bg-gray-800/50 border-gray-700/50'
              }
            `}
            whileHover={{ scale: 1.02 }}
          >
            <motion.div
              className={`w-6 h-6 rounded flex items-center justify-center ${
                tool.connected ? `bg-${tool.color}-500/20` : 'bg-gray-700'
              }`}
              animate={activeConnection === index && tool.connected ? {
                scale: [1, 1.2, 1]
              } : {}}
              transition={{ duration: 0.5 }}
            >
              <tool.icon className={`w-3 h-3 ${
                tool.connected ? `text-${tool.color}-400` : 'text-gray-500'
              }`} />
            </motion.div>
            <div className="flex-1">
              <p className="text-[10px] text-white">{tool.name}</p>
              <p className={`text-[8px] ${tool.connected ? 'text-emerald-400' : 'text-gray-500'}`}>
                {tool.connected ? 'Connected' : 'Not connected'}
              </p>
            </div>
            {tool.connected && (
              <motion.div
                className="w-2 h-2 bg-emerald-500 rounded-full"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
            )}
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

// ============================================================================
// Keyboard Shortcuts Demo Animation
// ============================================================================

export function KeyboardShortcutsDemo() {
  const [activeShortcut, setActiveShortcut] = useState(0);
  const [keyPressed, setKeyPressed] = useState<string | null>(null);

  useEffect(() => {
    const shortcutInterval = setInterval(() => {
      setActiveShortcut((prev) => (prev + 1) % 4);
    }, 2500);

    return () => clearInterval(shortcutInterval);
  }, []);

  useEffect(() => {
    const keys = ['/', '?', 'K', 'Esc'];
    setKeyPressed(keys[activeShortcut]);
    const timeout = setTimeout(() => setKeyPressed(null), 500);
    return () => clearTimeout(timeout);
  }, [activeShortcut]);

  const shortcuts = [
    { keys: ['/'], action: 'Focus chat input', icon: Search },
    { keys: ['?'], action: 'Show shortcuts', icon: Command },
    { keys: ['Ctrl', 'K'], action: 'Command palette', icon: Zap },
    { keys: ['Esc'], action: 'Close dialogs', icon: ArrowRight },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
        >
          <Command className="w-4 h-4 text-white" />
        </motion.div>
        <span className="text-white font-semibold text-sm">Keyboard Shortcuts</span>
      </motion.div>

      {/* Shortcuts List */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {shortcuts.map((shortcut, index) => (
          <motion.div
            key={shortcut.action}
            variants={slideInRight}
            className={`
              flex items-center justify-between p-2 rounded-lg border transition-all
              ${activeShortcut === index
                ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border-emerald-500/50'
                : 'bg-gray-800/50 border-gray-700/50'
              }
            `}
          >
            <div className="flex items-center gap-2">
              <shortcut.icon className={`w-3 h-3 ${
                activeShortcut === index ? 'text-emerald-400' : 'text-gray-500'
              }`} />
              <span className="text-[10px] text-gray-300">{shortcut.action}</span>
            </div>
            <div className="flex items-center gap-1">
              {shortcut.keys.map((key, keyIndex) => (
                <motion.kbd
                  key={key}
                  className={`
                    px-1.5 py-0.5 rounded text-[10px] font-mono
                    ${activeShortcut === index && keyPressed === key
                      ? 'bg-emerald-500 text-white'
                      : 'bg-gray-700 text-gray-300 border border-gray-600'
                    }
                  `}
                  animate={activeShortcut === index && keyPressed === key ? {
                    scale: [1, 1.2, 1],
                    y: [0, -2, 0]
                  } : {}}
                  transition={{ duration: 0.2 }}
                >
                  {key}
                </motion.kbd>
              ))}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Hint */}
      <motion.p
        className="text-[10px] text-gray-500 text-center mt-3"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        Press any key to see it in action
      </motion.p>
    </div>
  );
}

// ============================================================================
// Getting Started Demo Animation
// ============================================================================

export function GettingStartedDemo() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setStep((prev) => (prev + 1) % 4);
    }, 2500);

    return () => clearInterval(stepInterval);
  }, []);

  const steps = [
    { label: 'Sign Up', icon: Users, description: 'Create your account' },
    { label: 'Connect', icon: Database, description: 'Link your database' },
    { label: 'Configure', icon: Settings, description: 'Set up preferences' },
    { label: 'Start', icon: Zap, description: 'Begin managing inventory' },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Progress bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gray-800">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500"
          animate={{ width: `${((step + 1) / 4) * 100}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4 mt-2"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <Sparkles className="w-4 h-4 text-white" />
        </motion.div>
        <span className="text-white font-semibold text-sm">Getting Started</span>
      </motion.div>

      {/* Steps */}
      <div className="flex justify-between items-center mb-4">
        {steps.map((s, index) => (
          <motion.div
            key={s.label}
            className="flex flex-col items-center"
            animate={{
              scale: step === index ? 1.1 : 1,
              opacity: step >= index ? 1 : 0.5
            }}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              className={`
                w-10 h-10 rounded-full flex items-center justify-center mb-1
                ${step >= index
                  ? 'bg-gradient-to-br from-emerald-500 to-cyan-500'
                  : 'bg-gray-700'
                }
              `}
              animate={step === index ? {
                boxShadow: ['0 0 0 0 rgba(16, 185, 129, 0)', '0 0 15px 5px rgba(16, 185, 129, 0.3)', '0 0 0 0 rgba(16, 185, 129, 0)']
              } : {}}
              transition={{ duration: 1, repeat: step === index ? Infinity : 0 }}
            >
              <s.icon className="w-4 h-4 text-white" />
            </motion.div>
            <span className={`text-[8px] ${step >= index ? 'text-emerald-400' : 'text-gray-500'}`}>
              {s.label}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Current Step Details */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50"
        >
          <div className="flex items-center gap-2">
            {(() => {
              const StepIcon = steps[step].icon;
              return <StepIcon className="w-4 h-4 text-emerald-400" />;
            })()}
            <div>
              <p className="text-xs text-white font-medium">{steps[step].label}</p>
              <p className="text-[10px] text-gray-400">{steps[step].description}</p>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// Database Connection Demo Animation
// ============================================================================

export function DatabaseConnectionDemo() {
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'syncing'>('idle');

  useEffect(() => {
    const cycle = async () => {
      setStatus('idle');
      await new Promise(r => setTimeout(r, 1000));
      setStatus('connecting');
      await new Promise(r => setTimeout(r, 2000));
      setStatus('connected');
      await new Promise(r => setTimeout(r, 1500));
      setStatus('syncing');
      await new Promise(r => setTimeout(r, 2000));
    };

    cycle();
    const interval = setInterval(cycle, 7000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={status === 'connecting' ? { rotate: [0, 360] } : {}}
          transition={{ duration: 1, repeat: status === 'connecting' ? Infinity : 0, ease: 'linear' }}
        >
          <Database className="w-4 h-4 text-white" />
        </motion.div>
        <div>
          <span className="text-white font-semibold text-sm">Database</span>
          <motion.p
            className={`text-[10px] ${
              status === 'connected' || status === 'syncing' ? 'text-emerald-400' :
              status === 'connecting' ? 'text-cyan-400' : 'text-gray-400'
            }`}
          >
            {status === 'idle' && 'Ready to connect'}
            {status === 'connecting' && 'Connecting...'}
            {status === 'connected' && 'Connected'}
            {status === 'syncing' && 'Syncing data...'}
          </motion.p>
        </div>
      </motion.div>

      {/* Connection Animation */}
      <div className="relative h-24 flex items-center justify-center">
        {/* App Icon */}
        <motion.div
          className="absolute left-4 w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{ scale: status !== 'idle' ? [1, 1.05, 1] : 1 }}
          transition={{ duration: 1, repeat: status !== 'idle' ? Infinity : 0 }}
        >
          <Package className="w-6 h-6 text-white" />
        </motion.div>

        {/* Connection Line */}
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
          <motion.line
            x1="70"
            y1="48"
            x2="calc(100% - 70px)"
            y2="48"
            stroke="url(#dbGradient)"
            strokeWidth="3"
            strokeDasharray="8 4"
            animate={{
              opacity: status !== 'idle' ? 1 : 0.3,
              strokeDashoffset: status === 'syncing' ? [0, -24] : 0
            }}
            transition={status === 'syncing' ? { duration: 0.5, repeat: Infinity, ease: 'linear' } : {}}
          />
          <defs>
            <linearGradient id="dbGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
        </svg>

        {/* Database Icon */}
        <motion.div
          className={`
            absolute right-4 w-12 h-12 rounded-lg flex items-center justify-center
            ${status === 'connected' || status === 'syncing'
              ? 'bg-emerald-500/20 border-2 border-emerald-500'
              : 'bg-gray-700 border-2 border-gray-600'
            }
          `}
          animate={status === 'connected' || status === 'syncing' ? {
            boxShadow: ['0 0 0 0 rgba(16, 185, 129, 0)', '0 0 20px 10px rgba(16, 185, 129, 0.2)', '0 0 0 0 rgba(16, 185, 129, 0)']
          } : {}}
          transition={{ duration: 2, repeat: status === 'connected' || status === 'syncing' ? Infinity : 0 }}
        >
          <Database className={`w-6 h-6 ${
            status === 'connected' || status === 'syncing' ? 'text-emerald-400' : 'text-gray-400'
          }`} />
        </motion.div>

        {/* Data packets animation */}
        <AnimatePresence>
          {status === 'syncing' && [0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-emerald-400 rounded-full"
              initial={{ x: 60, opacity: 0 }}
              animate={{
                x: ['60px', 'calc(100% - 76px)'],
                opacity: [0, 1, 1, 0]
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.3,
                ease: 'linear'
              }}
              style={{ top: '50%', marginTop: '-4px' }}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Status */}
      <motion.div
        className="bg-gray-800/50 rounded-lg p-2 border border-gray-700/50 mt-2"
        animate={{ borderColor: status === 'connected' ? 'rgba(16, 185, 129, 0.5)' : 'rgba(55, 65, 81, 0.5)' }}
      >
        <div className="flex items-center gap-2">
          <motion.div
            className={`w-2 h-2 rounded-full ${
              status === 'connected' || status === 'syncing' ? 'bg-emerald-500' :
              status === 'connecting' ? 'bg-cyan-500' : 'bg-gray-500'
            }`}
            animate={{ scale: status !== 'idle' ? [1, 1.5, 1] : 1 }}
            transition={{ duration: 1, repeat: status !== 'idle' ? Infinity : 0 }}
          />
          <span className="text-[10px] text-gray-400">
            {status === 'idle' && 'Click to connect your database'}
            {status === 'connecting' && 'Establishing secure connection...'}
            {status === 'connected' && 'Connection established successfully'}
            {status === 'syncing' && 'Synchronizing inventory data...'}
          </span>
        </div>
      </motion.div>
    </div>
  );
}

// ============================================================================
// Settings Demo Animation
// ============================================================================

export function SettingsDemo() {
  const [activeSection, setActiveSection] = useState(0);
  const [toggleStates, setToggleStates] = useState([true, false, true]);

  useEffect(() => {
    const sectionInterval = setInterval(() => {
      setActiveSection((prev) => (prev + 1) % 3);
    }, 3000);

    return () => clearInterval(sectionInterval);
  }, []);

  useEffect(() => {
    // Toggle the active section's setting
    setToggleStates(prev => {
      const newStates = [...prev];
      newStates[activeSection] = !newStates[activeSection];
      return newStates;
    });
  }, [activeSection]);

  const settings = [
    { label: 'Dark Mode', description: 'Enable dark theme' },
    { label: 'Notifications', description: 'Push notifications' },
    { label: 'Auto-sync', description: 'Sync every 5 minutes' },
  ];

  return (
    <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-xl p-4 overflow-hidden">
      {/* Header */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex items-center gap-2 mb-4"
      >
        <motion.div
          className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center"
          animate={{ rotate: [0, 90, 180, 270, 360] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        >
          <Settings className="w-4 h-4 text-white" />
        </motion.div>
        <span className="text-white font-semibold text-sm">Settings</span>
      </motion.div>

      {/* Settings List */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {settings.map((setting, index) => (
          <motion.div
            key={setting.label}
            variants={slideInRight}
            className={`
              flex items-center justify-between p-3 rounded-lg border transition-all
              ${activeSection === index
                ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border-emerald-500/50'
                : 'bg-gray-800/50 border-gray-700/50'
              }
            `}
          >
            <div>
              <p className="text-xs text-white">{setting.label}</p>
              <p className="text-[10px] text-gray-500">{setting.description}</p>
            </div>
            <motion.button
              className={`
                w-10 h-5 rounded-full p-0.5 transition-colors
                ${toggleStates[index] ? 'bg-emerald-500' : 'bg-gray-600'}
              `}
              animate={{ backgroundColor: toggleStates[index] ? '#10b981' : '#4b5563' }}
            >
              <motion.div
                className="w-4 h-4 bg-white rounded-full shadow"
                animate={{ x: toggleStates[index] ? 20 : 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            </motion.button>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
