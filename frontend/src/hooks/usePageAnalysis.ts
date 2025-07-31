import { useState, useEffect } from 'react';
import { analyzePage, clearRag } from '@/lib/api';

type Status = 'idle' | 'analyzing' | 'chatting' | 'error';

const ANALYZED_URL_KEY = 'analyzedUrl';

export const usePageAnalysis = () => {
  const [status, setStatus] = useState<Status>('analyzing');
  const [error, setError] = useState<string | null>(null);
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);

  useEffect(() => {
    if (typeof chrome.tabs === 'undefined') {
        setStatus('chatting');
        setCurrentUrl('http://fake-dev-url.com');
        return;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const url = tabs[0]?.url;
      if (url) {
        setCurrentUrl(url);
        chrome.storage.local.get(ANALYZED_URL_KEY, (result) => {
          const analyzedUrl = result[ANALYZED_URL_KEY];
          if (analyzedUrl && analyzedUrl !== url) {
            clearRag(analyzedUrl).finally(() => {
                chrome.storage.local.remove(ANALYZED_URL_KEY);
                setStatus('idle');
            });
          } else if (analyzedUrl && analyzedUrl === url) {
            setStatus('chatting');
          } else {
            setStatus('idle');
          }
        });
      } else {
        setError("Could not determine current tab's URL.");
        setStatus('error');
      }
    });
  }, []);

  const handleAnalyze = async () => {
    if (!currentUrl) {
      setError('Could not get current URL.');
      setStatus('error');
      return;
    }
    setStatus('analyzing');
    setError(null);
    try {
      const result = await analyzePage(currentUrl);
      if (result.status === 'success') {
        setStatus('chatting');
        chrome.storage.local.set({ [ANALYZED_URL_KEY]: currentUrl });
      } else {
        setError(`Failed to analyze the page: ${result.message || 'Unknown error'}`);
        setStatus('error');
      }
    } catch (e: any) {
      setError(`An error occurred during analysis: ${e.message}`);
      setStatus('error');
    }
  };

  return { status, error, handleAnalyze };
};
