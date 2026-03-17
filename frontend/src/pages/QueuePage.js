import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic2, Clock, Plus, X, Music, User, Loader2, MessageSquare } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const QueuePage = () => {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addingToQueue, setAddingToQueue] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [songTitle, setSongTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [messageToAdmin, setMessageToAdmin] = useState('');

  const fetchQueue = async () => {
    try {
      const response = await axios.get(`${API}/queue`);
      setQueue(response.data);
    } catch (error) {
      console.error('Failed to fetch queue:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchQueue, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAddToQueue = async (e) => {
    e.preventDefault();
    if (!songTitle.trim() || !artist.trim()) {
      toast.error('Please enter both song title and artist');
      return;
    }

    setAddingToQueue(true);
    try {
      await axios.post(`${API}/queue`, {
        song_title: songTitle,
        artist: artist,
        message_to_admin: messageToAdmin.trim() || null
      });
      toast.success('Added to queue! Get ready to shine!');
      setSongTitle('');
      setArtist('');
      setMessageToAdmin('');
      setDialogOpen(false);
      fetchQueue();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to add to queue';
      toast.error(message);
    } finally {
      setAddingToQueue(false);
    }
  };

  const handleRemoveFromQueue = async (itemId) => {
    try {
      await axios.delete(`${API}/queue/${itemId}`);
      toast.success('Removed from queue');
      fetchQueue();
    } catch (error) {
      toast.error('Failed to remove from queue');
    }
  };

  const userInQueue = queue.find(item => item.user_id === user?.id);
  const currentSong = queue.find(item => item.status === 'current');

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading queue...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="queue-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white mb-2">
              Song <span className="text-gold">Queue</span>
            </h1>
            <p className="text-white/60">
              {queue.length} {queue.length === 1 ? 'performer' : 'performers'} waiting
            </p>
          </div>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button
                disabled={!!userInQueue}
                data-testid="add-to-queue-btn"
                className="btn-gold"
              >
                <Plus className="w-5 h-5 mr-2" />
                {userInQueue ? 'Already in Queue' : 'Join Queue'}
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-royal-paper border-white/10 text-white">
              <DialogHeader>
                <DialogTitle className="font-cinzel text-2xl text-gold">Add Your Song</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddToQueue} className="space-y-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Song Title</label>
                  <div className="relative">
                    <Music className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                    <input
                      type="text"
                      value={songTitle}
                      onChange={(e) => setSongTitle(e.target.value)}
                      placeholder="Enter song title"
                      data-testid="song-title-input"
                      className="w-full royal-input pl-12"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">Artist</label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                    <input
                      type="text"
                      value={artist}
                      onChange={(e) => setArtist(e.target.value)}
                      placeholder="Enter artist name"
                      data-testid="artist-input"
                      className="w-full royal-input pl-12"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    <MessageSquare className="inline w-4 h-4 mr-1" />
                    Message to KJ <span className="text-white/40">(optional)</span>
                  </label>
                  <div className="relative">
                    <textarea
                      value={messageToAdmin}
                      onChange={(e) => setMessageToAdmin(e.target.value.slice(0, 250))}
                      placeholder="Special requests, dedications, or notes for the KJ..."
                      data-testid="message-to-admin-input"
                      rows={3}
                      className="w-full royal-input resize-none"
                    />
                    <span className={`absolute bottom-2 right-3 text-xs ${messageToAdmin.length >= 240 ? 'text-red-400' : 'text-white/40'}`}>
                      {messageToAdmin.length}/250
                    </span>
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={addingToQueue}
                  data-testid="submit-song-btn"
                  className="w-full btn-gold"
                >
                  {addingToQueue ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Mic2 className="w-5 h-5 mr-2" />
                      Add to Queue
                    </>
                  )}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </motion.div>

        {/* Currently Performing */}
        {currentSong && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-6 border-gold/30 animate-gold-glow"
            data-testid="current-song"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-green-400 uppercase tracking-wider">Now Performing</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="p-4 bg-gold/10 rounded-xl">
                <Mic2 className="w-8 h-8 text-gold" />
              </div>
              <div className="flex-1">
                <h3 className="font-cinzel font-bold text-2xl text-white">{currentSong.user_name}</h3>
                <p className="text-gold text-lg">{currentSong.song_title}</p>
                <p className="text-white/60">{currentSong.artist}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Queue List */}
        <div className="space-y-4">
          <h2 className="font-cinzel font-bold text-xl text-white">Up Next</h2>
          
          {queue.filter(item => item.status === 'pending').length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass-card p-12 text-center"
            >
              <Mic2 className="w-12 h-12 text-white/20 mx-auto mb-4" />
              <p className="text-white/60 text-lg">No one in queue yet</p>
              <p className="text-white/40">Be the first to take the stage!</p>
            </motion.div>
          ) : (
            <AnimatePresence mode="popLayout">
              {queue
                .filter(item => item.status === 'pending')
                .map((item, index) => (
                  <motion.div
                    key={item.id}
                    layout
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className={`glass-card p-4 queue-item ${
                      item.user_id === user?.id ? 'border-gold/30' : ''
                    }`}
                    data-testid={`queue-item-${item.id}`}
                  >
                    <div className="flex items-center gap-4">
                      {/* Position */}
                      <div className="w-12 h-12 bg-white/5 rounded-lg flex items-center justify-center">
                        <span className="font-cinzel font-bold text-xl text-gold">{item.position}</span>
                      </div>

                      {/* Song Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-white truncate">{item.user_name}</h3>
                          {item.user_id === user?.id && (
                            <span className="text-xs bg-gold/20 text-gold px-2 py-0.5 rounded-full">You</span>
                          )}
                        </div>
                        <p className="text-gold truncate">{item.song_title}</p>
                        <p className="text-white/50 text-sm truncate">{item.artist}</p>
                      </div>

                      {/* Wait Time */}
                      <div className="text-right hidden sm:block">
                        <div className="flex items-center gap-1 text-white/60">
                          <Clock className="w-4 h-4" />
                          <span className="text-sm">~{item.estimated_wait} min</span>
                        </div>
                      </div>

                      {/* Remove Button (only for own song) */}
                      {item.user_id === user?.id && (
                        <button
                          onClick={() => handleRemoveFromQueue(item.id)}
                          data-testid={`remove-queue-${item.id}`}
                          className="p-2 text-white/40 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </motion.div>
                ))}
            </AnimatePresence>
          )}
        </div>

        {/* User's Position Info */}
        {userInQueue && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="fixed bottom-6 left-4 right-4 sm:left-auto sm:right-6 sm:w-80 glass-card p-4 border-gold/30"
            data-testid="user-queue-status"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gold/10 rounded-lg">
                <Clock className="w-5 h-5 text-gold" />
              </div>
              <div>
                <p className="text-white font-medium">You're #{userInQueue.position} in queue</p>
                <p className="text-white/60 text-sm">~{userInQueue.estimated_wait} min wait</p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </Layout>
  );
};

export default QueuePage;
