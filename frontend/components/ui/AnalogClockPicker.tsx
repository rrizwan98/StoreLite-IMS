'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Clock, X, Check, RotateCcw } from 'lucide-react';

interface AnalogClockPickerProps {
  value: string; // HH:mm format (24hr internally)
  onChange: (time: string) => void;
  className?: string;
}

type ClockMode = 'hours' | 'minutes';

export default function AnalogClockPicker({ value, onChange, className = '' }: AnalogClockPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<ClockMode>('hours');
  const [selectedHour, setSelectedHour] = useState(12);
  const [selectedMinute, setSelectedMinute] = useState(0);
  const [isPM, setIsPM] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const clockRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Parse initial value when opening
  useEffect(() => {
    if (isOpen && value) {
      const [hours, minutes] = value.split(':').map(Number);
      const hour12 = hours % 12 || 12;
      setSelectedHour(hour12);
      setSelectedMinute(minutes || 0);
      setIsPM(hours >= 12);
      setMode('hours');
    }
  }, [isOpen, value]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Calculate angle from center of clock
  const getAngleFromCenter = useCallback((clientX: number, clientY: number) => {
    if (!clockRef.current) return 0;
    const rect = clockRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const deltaX = clientX - centerX;
    const deltaY = clientY - centerY;
    let angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI) + 90;
    if (angle < 0) angle += 360;
    return angle;
  }, []);

  // Handle clock interaction (click or drag)
  const handleClockInteraction = useCallback((clientX: number, clientY: number) => {
    const angle = getAngleFromCenter(clientX, clientY);

    if (mode === 'hours') {
      // 12 hours, 30 degrees each
      let hour = Math.round(angle / 30);
      if (hour === 0) hour = 12;
      if (hour > 12) hour = hour - 12;
      setSelectedHour(hour);
    } else {
      // 60 minutes, 6 degrees each
      let minute = Math.round(angle / 6);
      if (minute === 60) minute = 0;
      setSelectedMinute(minute);
    }
  }, [mode, getAngleFromCenter]);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    handleClockInteraction(e.clientX, e.clientY);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      handleClockInteraction(e.clientX, e.clientY);
    }
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      // Auto-switch to minutes after selecting hour
      if (mode === 'hours') {
        setTimeout(() => setMode('minutes'), 200);
      }
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    const touch = e.touches[0];
    handleClockInteraction(touch.clientX, touch.clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isDragging) {
      const touch = e.touches[0];
      handleClockInteraction(touch.clientX, touch.clientY);
    }
  };

  const handleTouchEnd = () => {
    if (isDragging) {
      setIsDragging(false);
      if (mode === 'hours') {
        setTimeout(() => setMode('minutes'), 200);
      }
    }
  };

  // Calculate hand angle
  const getHandAngle = () => {
    if (mode === 'hours') {
      return (selectedHour % 12) * 30;
    }
    return selectedMinute * 6;
  };

  // Format display time
  const formatDisplayTime = () => {
    const hour = selectedHour.toString().padStart(2, '0');
    const minute = selectedMinute.toString().padStart(2, '0');
    const period = isPM ? 'PM' : 'AM';
    return `${hour}:${minute} ${period}`;
  };

  // Convert to 24hr format for onChange
  const get24HourTime = () => {
    let hour24 = selectedHour;
    if (isPM && selectedHour !== 12) {
      hour24 = selectedHour + 12;
    } else if (!isPM && selectedHour === 12) {
      hour24 = 0;
    }
    return `${hour24.toString().padStart(2, '0')}:${selectedMinute.toString().padStart(2, '0')}`;
  };

  // Handle OK click
  const handleConfirm = () => {
    onChange(get24HourTime());
    setIsOpen(false);
  };

  // Handle Reset
  const handleReset = () => {
    setSelectedHour(12);
    setSelectedMinute(0);
    setIsPM(false);
    setMode('hours');
  };

  // Format displayed value in input
  const formatInputValue = () => {
    if (!value) return '';
    const [hours, minutes] = value.split(':').map(Number);
    const hour12 = hours % 12 || 12;
    const period = hours >= 12 ? 'PM' : 'AM';
    return `${hour12.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${period}`;
  };

  // Generate clock numbers
  const renderClockNumbers = () => {
    const numbers = mode === 'hours'
      ? [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
      : [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55];

    return numbers.map((num, index) => {
      const angle = (index * 30 - 90) * (Math.PI / 180);
      const radius = 85;
      const x = 110 + radius * Math.cos(angle);
      const y = 110 + radius * Math.sin(angle);

      const isSelected = mode === 'hours'
        ? num === selectedHour
        : num === selectedMinute;

      return (
        <div
          key={num}
          className={`absolute w-8 h-8 flex items-center justify-center text-sm font-medium rounded-full transition-colors cursor-pointer
            ${isSelected ? 'bg-emerald-500 text-white' : 'text-gray-700 hover:bg-gray-100'}`}
          style={{
            left: `${x - 16}px`,
            top: `${y - 16}px`,
          }}
          onClick={() => {
            if (mode === 'hours') {
              setSelectedHour(num === 0 ? 12 : num);
              setTimeout(() => setMode('minutes'), 200);
            } else {
              setSelectedMinute(num);
            }
          }}
        >
          {mode === 'minutes' ? num.toString().padStart(2, '0') : num}
        </div>
      );
    });
  };

  return (
    <div className={`relative ${className}`}>
      {/* Input Display */}
      <div
        onClick={() => setIsOpen(true)}
        className="flex items-center w-full px-4 py-2.5 border border-gray-300 rounded-lg cursor-pointer hover:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-500 bg-white"
      >
        <Clock className="h-4 w-4 text-gray-400 mr-2" />
        <span className={`flex-1 ${value ? 'text-gray-900' : 'text-gray-400'}`}>
          {value ? formatInputValue() : 'Select time'}
        </span>
      </div>

      {/* Clock Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div
            ref={modalRef}
            className="bg-white rounded-2xl shadow-2xl w-[300px] overflow-hidden animate-in fade-in zoom-in-95 duration-200"
          >
            {/* Header with selected time */}
            <div className="bg-emerald-500 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="text-white">
                  <p className="text-xs opacity-80 mb-1">Selected Time</p>
                  <div className="flex items-baseline space-x-1">
                    <span
                      onClick={() => setMode('hours')}
                      className={`text-3xl font-bold cursor-pointer transition-opacity ${mode === 'hours' ? 'opacity-100' : 'opacity-60 hover:opacity-80'}`}
                    >
                      {selectedHour.toString().padStart(2, '0')}
                    </span>
                    <span className="text-3xl font-bold">:</span>
                    <span
                      onClick={() => setMode('minutes')}
                      className={`text-3xl font-bold cursor-pointer transition-opacity ${mode === 'minutes' ? 'opacity-100' : 'opacity-60 hover:opacity-80'}`}
                    >
                      {selectedMinute.toString().padStart(2, '0')}
                    </span>
                  </div>
                </div>
                {/* AM/PM Toggle */}
                <div className="flex flex-col space-y-1">
                  <button
                    onClick={() => setIsPM(false)}
                    className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                      !isPM ? 'bg-white text-emerald-600' : 'text-white/70 hover:text-white'
                    }`}
                  >
                    AM
                  </button>
                  <button
                    onClick={() => setIsPM(true)}
                    className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                      isPM ? 'bg-white text-emerald-600' : 'text-white/70 hover:text-white'
                    }`}
                  >
                    PM
                  </button>
                </div>
              </div>
            </div>

            {/* Clock Face */}
            <div className="p-4">
              <div
                ref={clockRef}
                className="relative w-[220px] h-[220px] mx-auto bg-gray-50 rounded-full border-4 border-gray-200 select-none"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
              >
                {/* Clock Numbers */}
                {renderClockNumbers()}

                {/* Center Dot */}
                <div className="absolute top-1/2 left-1/2 w-3 h-3 bg-emerald-500 rounded-full transform -translate-x-1/2 -translate-y-1/2 z-10" />

                {/* Clock Hand */}
                <div
                  className="absolute top-1/2 left-1/2 origin-bottom transition-transform duration-100"
                  style={{
                    width: '2px',
                    height: mode === 'hours' ? '60px' : '75px',
                    backgroundColor: '#10b981',
                    transform: `translateX(-50%) translateY(-100%) rotate(${getHandAngle()}deg)`,
                  }}
                >
                  {/* Hand End Circle */}
                  <div className="absolute -top-2 left-1/2 w-4 h-4 bg-emerald-500 rounded-full transform -translate-x-1/2" />
                </div>
              </div>

              {/* Mode Indicator */}
              <div className="flex justify-center mt-3 space-x-4">
                <span
                  onClick={() => setMode('hours')}
                  className={`text-sm font-medium cursor-pointer transition-colors ${
                    mode === 'hours' ? 'text-emerald-600' : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  Hours
                </span>
                <span className="text-gray-300">|</span>
                <span
                  onClick={() => setMode('minutes')}
                  className={`text-sm font-medium cursor-pointer transition-colors ${
                    mode === 'minutes' ? 'text-emerald-600' : 'text-gray-400 hover:text-gray-600'
                  }`}
                >
                  Minutes
                </span>
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="flex border-t border-gray-200">
              <button
                onClick={handleReset}
                className="flex-1 flex items-center justify-center py-3 text-gray-600 hover:bg-gray-50 transition-colors font-medium"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </button>
              <div className="w-px bg-gray-200" />
              <button
                onClick={handleConfirm}
                className="flex-1 flex items-center justify-center py-3 text-emerald-600 hover:bg-emerald-50 transition-colors font-medium"
              >
                <Check className="h-4 w-4 mr-2" />
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
