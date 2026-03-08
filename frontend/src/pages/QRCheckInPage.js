import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { QrCode, RefreshCw, Users, Clock, Download } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const FRONTEND_URL = window.location.origin;

const QRCheckInPage = () => {
  const [qrData, setQrData] = useState(null);
  const [todayCheckins, setTodayCheckins] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qrImageUrl, setQrImageUrl] = useState('');

  const fetchData = async () => {
    try {
      const [qrRes, checkinsRes] = await Promise.all([
        axios.get(`${API}/venue/qr-data`),
        axios.get(`${API}/admin/checkins/today`)
      ]);
      setQrData(qrRes.data);
      setTodayCheckins(checkinsRes.data);
      
      // Generate QR code image URL using a free QR API
      const checkinUrl = `${FRONTEND_URL}/checkin/${qrRes.data.venue_code}`;
      const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(checkinUrl)}&bgcolor=1A0B2E&color=FFD700`;
      setQrImageUrl(qrUrl);
    } catch (error) {
      console.error('Failed to fetch QR data:', error);
      toast.error('Failed to load QR code');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every minute
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleDownloadQR = () => {
    const link = document.createElement('a');
    link.href = qrImageUrl;
    link.download = `king-karaoke-checkin-${qrData?.date}.png`;
    link.click();
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading QR Code...</div>
        </div>
      </Layout>
    );
  }

  const checkinUrl = `${FRONTEND_URL}/checkin/${qrData?.venue_code}`;

  return (
    <Layout>
      <div className="space-y-8" data-testid="qr-checkin-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <QrCode className="w-6 h-6 text-gold" />
              <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white">
                QR <span className="text-gold">Check-In</span>
              </h1>
            </div>
            <p className="text-white/60">Display this QR code at the venue for customer check-ins</p>
          </div>
          <Button
            onClick={fetchData}
            data-testid="refresh-qr-btn"
            className="bg-white/5 border border-white/20 hover:bg-white/10 text-white"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* QR Code Display */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="glass-card p-8 text-center"
          >
            <h2 className="font-cinzel font-bold text-xl text-white mb-6">Scan to Check In</h2>
            
            {/* QR Code */}
            <div className="bg-white rounded-2xl p-4 inline-block mb-6">
              <img 
                src={qrImageUrl} 
                alt="Check-in QR Code"
                className="w-64 h-64 mx-auto"
                data-testid="qr-code-image"
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-white/60">
                <Clock className="w-4 h-4" />
                <span>Valid for: {qrData?.date}</span>
              </div>
              
              <p className="text-white/40 text-sm break-all px-4">
                {checkinUrl}
              </p>

              <Button
                onClick={handleDownloadQR}
                data-testid="download-qr-btn"
                className="btn-gold"
              >
                <Download className="w-4 h-4 mr-2" />
                Download QR Code
              </Button>
            </div>
          </motion.div>

          {/* Today's Check-ins */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="glass-card overflow-hidden"
          >
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <h2 className="font-cinzel font-bold text-lg text-white">Today's Check-ins</h2>
              <div className="flex items-center gap-2 bg-gold/10 px-3 py-1 rounded-full">
                <Users className="w-4 h-4 text-gold" />
                <span className="text-gold font-bold">{todayCheckins?.total_checkins || 0}</span>
              </div>
            </div>
            
            <div className="max-h-[400px] overflow-y-auto">
              {todayCheckins?.checkins?.length === 0 ? (
                <div className="p-8 text-center">
                  <Users className="w-10 h-10 text-white/20 mx-auto mb-3" />
                  <p className="text-white/60">No check-ins yet today</p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {todayCheckins?.checkins?.map((checkin, index) => (
                    <motion.div
                      key={checkin.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-white font-medium">{checkin.user_name}</p>
                        <p className="text-white/40 text-sm">
                          {new Date(checkin.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                      <span className="text-gold text-sm">+50 pts</span>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Instructions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card p-6"
        >
          <h3 className="font-cinzel font-bold text-lg text-white mb-4">How It Works</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-gold/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-gold font-bold text-xl">1</span>
              </div>
              <p className="text-white/80">Display QR code at entrance</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-gold/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-gold font-bold text-xl">2</span>
              </div>
              <p className="text-white/80">Customers scan with phone</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-gold/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-gold font-bold text-xl">3</span>
              </div>
              <p className="text-white/80">They earn +50 points instantly</p>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  );
};

export default QRCheckInPage;
