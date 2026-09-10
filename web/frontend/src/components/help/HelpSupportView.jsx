import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp, Mail, ExternalLink, CheckCircle2, X, Play, Landmark, Activity } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

const FAQ_ITEMS = [
  {
    id: 'faq_1',
    question: 'How do I start a classroom session?',
    answer: 'Select your active grades, subject, duration, and available resources in the Start Session form, then click "Start Session →". Saarthi will coordinate the initial plan for each grade.',
  },
  {
    id: 'faq_2',
    question: 'How does Saarthi choose activities?',
    answer: 'Saarthi checks curriculum position, past classroom history, available resources (tablets, TV, printer), and active constraints to generate balanced activities for each grade.',
  },
  {
    id: 'faq_3',
    question: 'How do I include a Government Session?',
    answer: 'Go to the Government Session tab, select "Add to Today\'s Session" on any official session, assign eligible grades, and it will automatically be included in today\'s classroom plan.',
  },
  {
    id: 'faq_4',
    question: 'Where can I see what each grade is doing?',
    answer: 'Visit the Activity page or Dashboard while a session is active to view current activities, student questions, and live progress across every grade.',
  },
  {
    id: 'faq_5',
    question: 'How do I end a session?',
    answer: 'Click the "End Session" button at the top right of the Dashboard active session view when your classroom time is complete.',
  },
  {
    id: 'faq_6',
    question: 'How do I mark attendance?',
    answer: 'Go to the Attendance page in the sidebar, select your grade, mark students as Present or Absent, and click "Save Attendance".',
  },
];

export default function HelpSupportView({ onNavigate = () => {} }) {
  const { t } = useTranslation();

  // Accordion state
  const [openFaqId, setOpenFaqId] = useState(null);

  // Modal & Toast state
  const [isSupportModalOpen, setIsSupportModalOpen] = useState(false);
  const [supportMessage, setSupportMessage] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const toggleFaq = (id) => {
    setOpenFaqId((prev) => (prev === id ? null : id));
  };

  const handleSendSupportRequest = (e) => {
    e.preventDefault();
    setIsSupportModalOpen(false);
    setSupportMessage('');
    setToastMessage('✓ Support request prepared');
    setTimeout(() => setToastMessage(null), 3500);
  };

  return (
    <div className="space-y-7 max-w-4xl relative">
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
          Help & Support
        </h1>
        <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
          Find answers or get help using Saarthi.
        </p>
      </div>

      {/* QUICK LINKS CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          onClick={() => onNavigate('dashboard')}
          className="liquid-glass-card rounded-[20px] p-5 border border-black/[0.08] dark:border-white/[0.10] space-y-2 cursor-pointer hover:border-black/20 dark:hover:border-white/20 transition-all group"
        >
          <div className="flex items-center justify-between">
            <Play className="w-5 h-5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <span className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] group-hover:underline">Open →</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Getting Started
            </h3>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
              Start your first classroom session.
            </p>
          </div>
        </div>

        <div
          onClick={() => onNavigate('government_session')}
          className="liquid-glass-card rounded-[20px] p-5 border border-black/[0.08] dark:border-white/[0.10] space-y-2 cursor-pointer hover:border-black/20 dark:hover:border-white/20 transition-all group"
        >
          <div className="flex items-center justify-between">
            <Landmark className="w-5 h-5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <span className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] group-hover:underline">Open →</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Government Sessions
            </h3>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
              Learn how to include government learning sessions.
            </p>
          </div>
        </div>

        <div
          onClick={() => onNavigate('activity')}
          className="liquid-glass-card rounded-[20px] p-5 border border-black/[0.08] dark:border-white/[0.10] space-y-2 cursor-pointer hover:border-black/20 dark:hover:border-white/20 transition-all group"
        >
          <div className="flex items-center justify-between">
            <Activity className="w-5 h-5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <span className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] group-hover:underline">Open →</span>
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Using Activities
            </h3>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
              Learn how Saarthi activities work.
            </p>
          </div>
        </div>
      </div>

      {/* QUICK HELP ACCORDIONS */}
      <div className="space-y-3">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
            Frequently Asked Questions
          </h2>
          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            Short, teacher-friendly answers to common questions.
          </p>
        </div>

        <div className="liquid-glass-card rounded-[24px] overflow-hidden border border-black/[0.08] dark:border-white/[0.10] divide-y divide-black/[0.05] dark:divide-white/[0.07]">
          {FAQ_ITEMS.map((faq) => {
            const isOpen = openFaqId === faq.id;
            return (
              <div key={faq.id} className="p-4 space-y-2">
                <button
                  type="button"
                  onClick={() => toggleFaq(faq.id)}
                  className="w-full flex items-center justify-between gap-3 text-left cursor-pointer focus:outline-none"
                >
                  <span className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {faq.question}
                  </span>
                  <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[#6E6E6E] dark:text-[#A3A3A3]">
                    {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {isOpen && (
                  <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed pt-1 animate-fade-in">
                    {faq.answer}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* CONTACT SUPPORT SECTION */}
      <div className="liquid-glass-card rounded-[24px] p-6 space-y-3 border border-black/[0.08] dark:border-white/[0.10]">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-base font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Need more help?
            </h2>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
              We're here to help you get the most out of Saarthi in your classroom.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsSupportModalOpen(true)}
            className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold inline-flex items-center gap-2 cursor-pointer shrink-0"
          >
            <Mail className="w-4 h-4" />
            <span>Contact Support</span>
          </button>
        </div>
      </div>

      {/* CONTACT SUPPORT MODAL */}
      {isSupportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity duration-300"
            onClick={() => setIsSupportModalOpen(false)}
          />

          <div className="relative w-full max-w-md liquid-glass-card rounded-[28px] p-6 sm:p-7 z-10 shadow-2xl space-y-5">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
              <div>
                <h3 className="text-lg font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                  Support Request
                </h3>
                <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
                  Send a message to our support team.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsSupportModalOpen(false)}
                className="liquid-glass-btn-icon w-8 h-8 rounded-full flex items-center justify-center cursor-pointer text-[#6E6E6E]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSendSupportRequest} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Email</label>
                <input
                  type="email"
                  readOnly
                  value="support@saarthi.education"
                  className="w-full px-3 py-2 rounded-xl bg-black/[0.03] dark:bg-white/[0.03] border border-black/10 dark:border-white/15 text-[#6E6E6E] dark:text-[#A3A3A3] font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Subject</label>
                <input
                  type="text"
                  readOnly
                  value="Saarthi Support Request"
                  className="w-full px-3 py-2 rounded-xl bg-black/[0.03] dark:bg-white/[0.03] border border-black/10 dark:border-white/15 text-[#6E6E6E] dark:text-[#A3A3A3] font-medium"
                />
              </div>

              <div className="space-y-1">
                <label htmlFor="support-message" className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Message</label>
                <textarea
                  id="support-message"
                  required
                  rows={4}
                  value={supportMessage}
                  onChange={(e) => setSupportMessage(e.target.value)}
                  placeholder="Describe what you need help with..."
                  className="w-full px-3 py-2 rounded-xl bg-white/80 dark:bg-white/10 border border-black/10 dark:border-white/15 text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none resize-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5 border-t border-black/[0.06] dark:border-white/[0.08]">
                <button
                  type="button"
                  onClick={() => setIsSupportModalOpen(false)}
                  className="liquid-glass-btn-secondary px-4 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Send Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
