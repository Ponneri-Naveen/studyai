import React from 'react';
import { Calendar, Clock, AlertTriangle } from 'lucide-react';

const Schedule = () => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Study Schedule
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Keep track of upcoming study plans, revision timers, and space repetition schedules.
        </p>
      </div>

      {/* Basic Mock Calendar/List Scaffold */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-dark-900 border border-dark-850 p-6 rounded-2xl">
          <h2 className="text-base font-bold text-white mb-6 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary-400" />
            Upcoming Sessions
          </h2>
          <div className="text-center py-12">
            <Clock className="w-10 h-10 text-dark-600 mx-auto mb-3" />
            <p className="text-sm text-dark-400 font-semibold">Your schedule is clear</p>
            <p className="text-xs text-dark-500 mt-1">Once you request study schedules, they will appear here.</p>
          </div>
        </div>

        <div className="bg-dark-900 border border-dark-850 p-6 rounded-2xl space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-primary-400" />
            Reminders
          </h2>
          <div className="p-3 bg-dark-850 rounded-xl border border-dark-800">
            <p className="text-xs text-dark-300">Set study reminders to optimize learning intervals.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Schedule;
