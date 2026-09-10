import React, { useState } from 'react';
import { CheckCircle2, Check } from 'lucide-react';

const ALL_GRADES = ['1', '2', '3', '4', '5', '6', '7', '8'];

const INITIAL_STUDENTS_BY_GRADE = {
  '3': [
    { id: '3_1', name: 'Sarah Patel', status: 'present' },
    { id: '3_2', name: 'Rahul Sharma', status: 'present' },
    { id: '3_3', name: 'Aarav Mehta', status: 'absent' },
    { id: '3_4', name: 'Diya Shah', status: 'present' },
    { id: '3_5', name: 'Vivaan Joshi', status: 'present' },
    { id: '3_6', name: 'Ananya Rao', status: 'present' },
    { id: '3_7', name: 'Ishaan Verma', status: 'present' },
    { id: '3_8', name: 'Priya Nair', status: 'present' },
    { id: '3_9', name: 'Kian Kapoor', status: 'absent' },
    { id: '3_10', name: 'Myra Deshmukh', status: 'present' },
    { id: '3_11', name: 'Aditya Bhat', status: 'present' },
    { id: '3_12', name: 'Riya Kulkarni', status: 'present' },
    { id: '3_13', name: 'Siddharth Iyer', status: 'present' },
    { id: '3_14', name: 'Kavya Singh', status: 'present' },
    { id: '3_15', name: 'Arjun Pandey', status: 'present' },
    { id: '3_16', name: 'Tanvi Saxena', status: 'present' },
    { id: '3_17', name: 'Rohan Gupta', status: 'present' },
    { id: '3_18', name: 'Neha Pillai', status: 'present' },
    { id: '3_19', name: 'Dev Sen', status: 'present' },
    { id: '3_20', name: 'Tara Agarwal', status: 'present' },
    { id: '3_21', name: 'Yash Malhotra', status: 'present' },
    { id: '3_22', name: 'Isha Reddy', status: 'present' },
    { id: '3_23', name: 'Kabir Das', status: 'present' },
    { id: '3_24', name: 'Avani Tripathi', status: 'present' },
  ],
  '4': [
    { id: '4_1', name: 'Arjun Patel', status: 'present' },
    { id: '4_2', name: 'Riya Sharma', status: 'present' },
    { id: '4_3', name: 'Dev Kumar', status: 'absent' },
    { id: '4_4', name: 'Sneha Gupta', status: 'present' },
    { id: '4_5', name: 'Aditya Varma', status: 'present' },
    { id: '4_6', name: 'Tanvi Reddy', status: 'present' },
    { id: '4_7', name: 'Vihaan Sinha', status: 'present' },
    { id: '4_8', name: 'Shruti Mishra', status: 'present' },
    { id: '4_9', name: 'Manav Shah', status: 'present' },
    { id: '4_10', name: 'Bhavya Jain', status: 'present' },
    { id: '4_11', name: 'Dhruv Gill', status: 'present' },
    { id: '4_12', name: 'Meera Trivedi', status: 'present' },
    { id: '4_13', name: 'Pranav Roy', status: 'present' },
    { id: '4_14', name: 'Sanvi Bose', status: 'present' },
    { id: '4_15', name: 'Varun Hegde', status: 'present' },
    { id: '4_16', name: 'Nisha Thakur', status: 'present' },
    { id: '4_17', name: 'Ayaan Nambiar', status: 'present' },
    { id: '4_18', name: 'Pari Somani', status: 'present' },
    { id: '4_19', name: 'Rehan Qureshi', status: 'present' },
    { id: '4_20', name: 'Siya Bannerjee', status: 'present' },
  ],
  '5': [
    { id: '5_1', name: 'Kabir Mehta', status: 'present' },
    { id: '5_2', name: 'Isha Sen', status: 'present' },
    { id: '5_3', name: 'Siddharth Roy', status: 'present' },
    { id: '5_4', name: 'Neha Choudhury', status: 'absent' },
    { id: '5_5', name: 'Rohan Das', status: 'present' },
    { id: '5_6', name: 'Trisha Chawla', status: 'present' },
    { id: '5_7', name: 'Kushal Kaushik', status: 'present' },
    { id: '5_8', name: 'Nidhi Merchant', status: 'present' },
    { id: '5_9', name: 'Reyansh Sethi', status: 'present' },
    { id: '5_10', name: 'Janhavi Menon', status: 'present' },
    { id: '5_11', name: 'Yashvardhan Tomar', status: 'present' },
    { id: '5_12', name: 'Alisha Merchant', status: 'present' },
    { id: '5_13', name: 'Tushar Ahuja', status: 'present' },
    { id: '5_14', name: 'Anika Grover', status: 'present' },
    { id: '5_15', name: 'Harsh Vardhan', status: 'present' },
    { id: '5_16', name: 'Juhi Phadke', status: 'present' },
    { id: '5_17', name: 'Nakul Bhasin', status: 'present' },
    { id: '5_18', name: 'Ojaswini Puri', status: 'present' },
    { id: '5_19', name: 'Parth Soni', status: 'present' },
    { id: '5_20', name: 'Riddhi Wadhwa', status: 'present' },
    { id: '5_21', name: 'Samarth Lodha', status: 'present' },
    { id: '5_22', name: 'Zoya Khan', status: 'present' },
  ],
};

export default function AttendanceView({ onSaveAttendance = () => {} }) {
  const [selectedGrade, setSelectedGrade] = useState('3');
  const [studentsByGrade, setStudentsByGrade] = useState(INITIAL_STUDENTS_BY_GRADE);
  const [toastMessage, setToastMessage] = useState(null);

  // Get current grade students, fallback to default generated list
  const currentStudents = studentsByGrade[selectedGrade] || [
    { id: `${selectedGrade}_1`, name: `Student A (Grade ${selectedGrade})`, status: 'present' },
    { id: `${selectedGrade}_2`, name: `Student B (Grade ${selectedGrade})`, status: 'present' },
    { id: `${selectedGrade}_3`, name: `Student C (Grade ${selectedGrade})`, status: 'present' },
    { id: `${selectedGrade}_4`, name: `Student D (Grade ${selectedGrade})`, status: 'present' },
    { id: `${selectedGrade}_5`, name: `Student E (Grade ${selectedGrade})`, status: 'absent' },
  ];

  const handleStatusChange = (studentId, newStatus) => {
    setStudentsByGrade((prev) => {
      const list = prev[selectedGrade] || currentStudents;
      const updated = list.map((s) => (s.id === studentId ? { ...s, status: newStatus } : s));
      return {
        ...prev,
        [selectedGrade]: updated,
      };
    });
  };

  const handleMarkAllPresent = () => {
    setStudentsByGrade((prev) => {
      const list = prev[selectedGrade] || currentStudents;
      const updated = list.map((s) => ({ ...s, status: 'present' }));
      return {
        ...prev,
        [selectedGrade]: updated,
      };
    });
  };

  const handleSaveAttendance = () => {
    onSaveAttendance();
    setToastMessage(`✓ Attendance saved for Grade ${selectedGrade}`);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const totalStudents = currentStudents.length;
  const presentCount = currentStudents.filter((s) => s.status === 'present').length;
  const absentCount = currentStudents.filter((s) => s.status === 'absent').length;

  return (
    <div className="space-y-6 relative">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 liquid-glass-card rounded-2xl px-4 py-3 shadow-xl border border-emerald-500/30 flex items-center gap-3 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {toastMessage}
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
          Attendance
        </h1>
        <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
          Mark and review today's student attendance.
        </p>
      </div>

      {/* TODAY & GRADE SELECTOR BAR */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] flex items-center gap-2">
            <span className="text-[#6E6E6E] dark:text-[#A3A3A3] uppercase tracking-wider text-[11px]">Today:</span>
            <span>September 9, 2026</span>
          </div>
          <div className="h-4 w-px bg-black/10 dark:bg-white/10" />
          <div className="flex items-center gap-2">
            <label htmlFor="attendance-grade-select" className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
              GRADE
            </label>
            <select
              id="attendance-grade-select"
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              className="bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
            >
              {ALL_GRADES.map((g) => (
                <option key={g} value={g} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                  Grade {g}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={handleMarkAllPresent}
          className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer"
        >
          <Check className="w-3.5 h-3.5 text-emerald-500" />
          <span>Mark all present</span>
        </button>
      </div>

      {/* SUMMARY & PRIMARY SAVE BAR */}
      <div className="liquid-glass-card rounded-[20px] p-4 border border-black/[0.08] dark:border-white/[0.10] flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4 text-xs">
          <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
            Grade {selectedGrade} · Today
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-black/5 dark:bg-white/10 text-[#0A0A0A] dark:text-[#F5F5F5]">
              {totalStudents} students
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/25">
              {presentCount} present
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-500/25">
              {absentCount} absent
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSaveAttendance}
          className="liquid-glass-btn-primary px-5 py-2 rounded-xl text-xs font-semibold cursor-pointer"
        >
          Save Attendance
        </button>
      </div>

      {/* STUDENT ATTENDANCE LIST */}
      <div className="liquid-glass-card rounded-[24px] overflow-hidden border border-black/[0.08] dark:border-white/[0.10] divide-y divide-black/[0.05] dark:divide-white/[0.07]">
        {currentStudents.map((student) => {
          const isPresent = student.status === 'present';
          return (
            <div
              key={student.id}
              className="p-4 flex items-center justify-between gap-4 transition-colors duration-150 hover:bg-black/[0.01] dark:hover:bg-white/[0.02]"
            >
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  isPresent
                    ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                    : 'bg-rose-500/15 text-rose-600 dark:text-rose-400'
                }`}>
                  {student.name.charAt(0)}
                </div>
                <span className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                  {student.name}
                </span>
              </div>

              {/* Tactile Control Buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleStatusChange(student.id, 'present')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                    isPresent
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-700 dark:text-emerald-300 font-bold shadow-xs'
                      : 'liquid-glass-btn-secondary opacity-70 hover:opacity-100'
                  }`}
                >
                  Present
                </button>
                <button
                  type="button"
                  onClick={() => handleStatusChange(student.id, 'absent')}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                    !isPresent
                      ? 'bg-rose-500/20 border-rose-500/40 text-rose-700 dark:text-rose-300 font-bold shadow-xs'
                      : 'liquid-glass-btn-secondary opacity-70 hover:opacity-100'
                  }`}
                >
                  Absent
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
