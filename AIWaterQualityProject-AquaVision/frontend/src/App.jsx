import React, { useState, useEffect } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/views/DashboardView';
import TankerManagementView from './components/views/TankerManagementView';
import LiveMonitoringView from './components/views/LiveMonitoringView';
import AnalyticsView from './components/views/AnalyticsView';
import AIInsightsView from './components/views/AIInsightsView';
import AIAssistantView from './components/views/AIAssistantView';
import ReportsView from './components/views/ReportsView';
import ActivityView from './components/views/ActivityView';
import SettingsView from './components/views/SettingsView';
import ReportPreviewModal from './components/modals/ReportPreviewModal';
import GenerateReportModal from './components/modals/GenerateReportModal';
import EditProfileModal from './components/modals/EditProfileModal';
import AddTankerModal from './components/modals/AddTankerModal';
import ManualReadingModal from './components/modals/ManualReadingModal';
import {
  fetchTankers,
  fetchReports,
  fetchAnalytics,
  fetchProfile,
} from './services/api';

export default function App() {
  const [currentView, setCurrentView] = useState(() => {
    const hash = window.location.hash.replace('#', '').trim();
    const validViews = ['dashboard', 'tankers', 'live', 'analytics', 'ai-insights', 'ai-assistant', 'reports', 'activity', 'settings'];
    return validViews.includes(hash) ? hash : 'dashboard';
  });
  const [tankers, setTankers] = useState([]);
  const [selectedTanker, setSelectedTanker] = useState(null);
  const [reports, setReports] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [profile, setProfile] = useState({
    name: 'Ali Hassan',
    designation: 'Research Developer',
    role: 'Lead Full-Stack & AI Engineer',
    organization: 'AquaVision University Project',
    avatar_initials: 'AH',
  });

  // Modals state
  const [selectedReport, setSelectedReport] = useState(null);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
  const [targetTankerForReport, setTargetTankerForReport] = useState(null);
  const [isEditProfileOpen, setIsEditProfileOpen] = useState(false);
  const [isAddTankerOpen, setIsAddTankerOpen] = useState(false);
  const [isManualReadingOpen, setIsManualReadingOpen] = useState(false);
  const [targetTankerForReading, setTargetTankerForReading] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [tData, rData, aData, pData] = await Promise.all([
        fetchTankers().catch(() => []),
        fetchReports().catch(() => []),
        fetchAnalytics().catch(() => null),
        fetchProfile().catch(() => null),
      ]);

      if (Array.isArray(tData)) {
        setTankers(tData);
        if (tData.length > 0 && !selectedTanker) {
          setSelectedTanker(tData[0]);
        }
      }
      if (Array.isArray(rData)) {
        setReports(rData);
      }
      if (aData) {
        setAnalyticsData(aData);
      }
      if (pData) {
        setProfile(pData);
      }
    } catch (err) {
      console.error('Initial data load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '').trim();
      const validViews = ['dashboard', 'tankers', 'live', 'analytics', 'ai-insights', 'ai-assistant', 'reports', 'activity', 'settings'];
      if (validViews.includes(hash)) {
        setCurrentView(hash);
      }
    };
    window.addEventListener('hashchange', onHashChange);

    // Synchronize telemetry polling every 25 seconds
    const timer = setInterval(() => {
      fetchTankers().then((tData) => {
        if (Array.isArray(tData)) {
          setTankers(tData);
          setSelectedTanker((prev) => {
            if (!prev) return tData[0];
            return tData.find((t) => t.id === prev.id) || tData[0];
          });
        }
      }).catch(() => {});
      fetchReports().then((rData) => {
        if (Array.isArray(rData)) setReports(rData);
      }).catch(() => {});
    }, 25000);

    return () => {
      window.removeEventListener('hashchange', onHashChange);
      clearInterval(timer);
    };
  }, []);

  // Modal openers
  const openReportModal = (tankerId = null) => {
    setTargetTankerForReport(tankerId);
    setIsGenerateModalOpen(true);
  };

  const openManualReading = (tankerId = null) => {
    setTargetTankerForReading(tankerId);
    setIsManualReadingOpen(true);
  };

  // State handlers
  const handleReportGenerated = (newReport) => {
    setReports((prev) => [newReport, ...prev.filter((r) => r.id !== newReport.id)]);
    setSelectedReport(newReport);
  };

  const handleTankerCreated = (newTanker) => {
    setTankers((prev) => [...prev, newTanker]);
    setSelectedTanker(newTanker);
  };

  const handleTankerDeleted = (deletedId) => {
    setTankers((prev) => {
      const remaining = prev.filter((t) => t.id !== deletedId);
      if (selectedTanker?.id === deletedId) {
        setSelectedTanker(remaining[0] || null);
      }
      return remaining;
    });
  };

  const handleReadingUpdated = (updatedTanker) => {
    setTankers((prev) =>
      prev.map((t) => (t.id === updatedTanker.id ? updatedTanker : t))
    );
    if (selectedTanker?.id === updatedTanker.id) {
      setSelectedTanker(updatedTanker);
    }
    fetchAnalytics().then(setAnalyticsData).catch(() => {});
  };

  const handleProfileUpdated = (updatedProfile) => {
    setProfile(updatedProfile);
  };

  return (
    <ErrorBoundary>
      <div className="bg-brand-canvas text-brand-dark min-h-screen flex antialiased">
        {/* Navigation Sidebar */}
        <Sidebar
          currentView={currentView}
          setCurrentView={setCurrentView}
          reportsCount={reports.length}
          tankersCount={tankers.length}
        />

        {/* Main Content Area */}
        <div className="pl-72 flex-1 flex flex-col min-w-0">
          <Header
            profile={profile}
            currentView={currentView}
            setCurrentView={setCurrentView}
            openReportModal={() => openReportModal()}
            onOpenEditProfile={() => setIsEditProfileOpen(true)}
          />

          <main className={`${currentView === 'ai-assistant' ? 'p-3 sm:p-4 pb-3 sm:pb-4 flex-1 max-w-7xl w-full mx-auto flex flex-col h-[calc(100vh-4rem)]' : 'p-8 pb-16 flex-1 max-w-7xl w-full mx-auto'}`}>
            {currentView === 'dashboard' && (
              <DashboardView
                tankers={tankers}
                reports={reports}
                profile={profile}
                setCurrentView={setCurrentView}
                openReportModal={openReportModal}
                setSelectedReport={setSelectedReport}
                onSelectTanker={(t) => {
                  setSelectedTanker(t);
                  setCurrentView('live');
                }}
                onOpenAddTanker={() => setIsAddTankerOpen(true)}
                onOpenManualReading={() => openManualReading()}
              />
            )}

            {currentView === 'tankers' && (
              <TankerManagementView
                tankers={tankers}
                onOpenAddTanker={() => setIsAddTankerOpen(true)}
                onOpenManualReading={() => openManualReading()}
                onOpenGenerateReport={openReportModal}
                onTankerDeleted={handleTankerDeleted}
                onSelectTanker={(id) => {
                  const t = tankers.find((item) => item.id === id);
                  if (t) setSelectedTanker(t);
                  setCurrentView('live');
                }}
              />
            )}

            {currentView === 'live' && (
              <LiveMonitoringView
                tankers={tankers}
                selectedTanker={selectedTanker}
                setSelectedTanker={setSelectedTanker}
                openReportModal={openReportModal}
                onOpenManualReading={openManualReading}
              />
            )}

            {currentView === 'analytics' && (
              <AnalyticsView
                analyticsData={analyticsData}
                tankers={tankers}
              />
            )}

            {currentView === 'ai-insights' && (
              <AIInsightsView openReportModal={openReportModal} />
            )}

            {currentView === 'ai-assistant' && (
              <AIAssistantView
                tankers={tankers}
                selectedTanker={selectedTanker}
                setSelectedTanker={setSelectedTanker}
                setSelectedReport={setSelectedReport}
                onNewReportGenerated={handleReportGenerated}
                profile={profile}
              />
            )}

            {currentView === 'reports' && (
              <ReportsView
                reports={reports}
                openReportModal={openReportModal}
                setSelectedReport={setSelectedReport}
              />
            )}

            {currentView === 'activity' && <ActivityView />}

            {currentView === 'settings' && (
              <SettingsView
                profile={profile}
                onOpenEditProfile={() => setIsEditProfileOpen(true)}
                tankers={tankers}
                reports={reports}
              />
            )}
          </main>
        </div>

        {/* Global Modals */}
        {selectedReport && (
          <ReportPreviewModal
            report={selectedReport}
            onClose={() => setSelectedReport(null)}
          />
        )}

        {isGenerateModalOpen && (
          <GenerateReportModal
            tankers={tankers}
            initialTankerId={targetTankerForReport}
            onClose={() => setIsGenerateModalOpen(false)}
            onReportGenerated={handleReportGenerated}
          />
        )}

        {isEditProfileOpen && (
          <EditProfileModal
            profile={profile}
            onClose={() => setIsEditProfileOpen(false)}
            onProfileUpdated={handleProfileUpdated}
          />
        )}

        {isAddTankerOpen && (
          <AddTankerModal
            onClose={() => setIsAddTankerOpen(false)}
            onTankerCreated={handleTankerCreated}
          />
        )}

        {isManualReadingOpen && (
          <ManualReadingModal
            tankers={tankers}
            initialTankerId={targetTankerForReading}
            onClose={() => setIsManualReadingOpen(false)}
            onReadingAdded={handleReadingUpdated}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
