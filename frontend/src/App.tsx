import { usePageAnalysis } from './hooks/usePageAnalysis';
import { Button } from './components/ui/button';
import { ButtonLoading } from './components/ui/buttonloading';
import { ChatView } from './components/ChatView';
import './App.css';

function App() {
  const { status, error, handleAnalyze } = usePageAnalysis();

  const renderContent = () => {
    switch (status) {
      case 'idle':
        return (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <h1 className="text-xl font-bold">Page Pilot</h1>
            <p className="text-muted-foreground">Analyze this page to start chatting with an AI assistant about its content.</p>
            <Button onClick={handleAnalyze}>Analyze Page</Button>
          </div>
        );
      case 'analyzing':
        return (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <h1 className="text-xl font-bold">Analyzing Page...</h1>
            <p className="text-muted-foreground">Please wait while we process the content.</p>
            <ButtonLoading />
          </div>
        );
      case 'chatting':
        return <ChatView />;
      case 'error':
        return (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <h1 className="text-xl font-bold text-destructive">Analysis Failed</h1>
            <p className="text-muted-foreground text-sm">{error}</p>
            <Button onClick={handleAnalyze} variant="outline">Try Again</Button>
          </div>
        );
      default:
        return (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
                <h1 className="text-xl font-bold">Loading...</h1>
            </div>
        );
    }
  };

  return (
    <main className="w-[380px] h-[500px] p-4 bg-background text-foreground flex flex-col">
      {renderContent()}
    </main>
  );
}

export default App;