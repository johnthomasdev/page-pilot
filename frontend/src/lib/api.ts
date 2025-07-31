import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const analyzePage = async (url: string) => {
  const response = await axios.post(`${API_BASE_URL}/analyze`, { url });
  return response.data;
};

export const chatWithRag = async (question: string) => {
  const response = await axios.post(`${API_BASE_URL}/chat`, { question });
  return response.data;
};

export const clearRag = async (url: string) => {
  const response = await axios.delete(`${API_BASE_URL}/clear`, { data: { url } });
  return response.data;
};
