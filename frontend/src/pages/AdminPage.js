import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, Users, Mic2, CheckCircle, XCircle, Play, 
  Plus, Minus, Crown, RefreshCw, UserCheck 
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPage = () => {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [queueRes, usersRes, statsRes] = await Promise.all([
        axios.get(`${API}/queue`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/stats`)
      ]);
      setQueue(queueRes.data);
      setUsers(usersRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const handleCompleteSong = async (itemId) => {
    try {
      await axios.post(`${API}/admin/queue/${itemId}/complete`);
      toast.success('Song completed! Points awarded.');
      fetchData();
    } catch (error) {
      toast.error('Failed to complete song');
    }
  };

  const handleSetCurrent = async (itemId) => {
    try {
      await axios.post(`${API}/admin/queue/${itemId}/set-current`);
      toast.success('Set as current performer');
      fetchData();
    } catch (error) {
      toast.error('Failed to set current');
    }
  };

  const handleRemoveFromQueue = async (itemId) => {
    try {
      await axios.delete(`${API}/queue/${itemId}`);
      toast.success('Removed from queue');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove');
    }
  };

  const handleAdjustPoints = async (userId, points) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/points?points=${points}`);
      toast.success(`${points > 0 ? 'Added' : 'Removed'} ${Math.abs(points)} points`);
      fetchData();
    } catch (error) {
      toast.error('Failed to adjust points');
    }
  };

  const handleToggleAdmin = async (userId) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/toggle-admin`);
      toast.success('Admin status updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to toggle admin');
    }
  };

  const currentSong = queue.find(item => item.status === 'current');
  const pendingQueue = queue.filter(item => item.status === 'pending');

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-gold animate-pulse font-cinzel text-2xl">Loading admin panel...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8" data-testid="admin-page">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-6 h-6 text-gold" />
              <h1 className="font-cinzel font-bold text-3xl sm:text-4xl text-white">
                Admin <span className="text-gold">Panel</span>
              </h1>
            </div>
            <p className="text-white/60">Manage queue, users, and rewards</p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            data-testid="refresh-btn"
            className="bg-white/5 border border-white/20 hover:bg-white/10 text-white"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </motion.div>

        {/* Stats Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-4"
          data-testid="admin-stats"
        >
          <div className="stat-card">
            <div className="stat-value">{stats?.total_users || 0}</div>
            <div className="stat-label">Total Users</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats?.total_songs_performed || 0}</div>
            <div className="stat-label">Songs Done</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{queue.length}</div>
            <div className="stat-label">In Queue</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{users.filter(u => u.is_admin).length}</div>
            <div className="stat-label">Admins</div>
          </div>
        </motion.div>

        {/* Tabs */}
        <Tabs defaultValue="queue" className="w-full">
          <TabsList className="w-full sm:w-auto bg-royal-paper border border-white/10">
            <TabsTrigger 
              value="queue" 
              data-testid="queue-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Mic2 className="w-4 h-4 mr-2" />
              Queue
            </TabsTrigger>
            <TabsTrigger 
              value="users"
              data-testid="users-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
          </TabsList>

          {/* Queue Management */}
          <TabsContent value="queue" className="mt-6 space-y-6">
            {/* Current Performer */}
            {currentSong && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass-card p-6 border-gold/30"
                data-testid="admin-current-song"
              >
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-green-400 uppercase tracking-wider">Now Performing</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gold/10 rounded-xl">
                      <Mic2 className="w-6 h-6 text-gold" />
                    </div>
                    <div>
                      <h3 className="font-cinzel font-bold text-xl text-white">{currentSong.user_name}</h3>
                      <p className="text-gold">{currentSong.song_title} - {currentSong.artist}</p>
                    </div>
                  </div>
                  <Button
                    onClick={() => handleCompleteSong(currentSong.id)}
                    data-testid="complete-song-btn"
                    className="btn-gold"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Complete
                  </Button>
                </div>
              </motion.div>
            )}

            {/* Pending Queue */}
            <div>
              <h2 className="font-cinzel font-bold text-xl text-white mb-4">
                Up Next ({pendingQueue.length})
              </h2>
              {pendingQueue.length === 0 ? (
                <div className="glass-card p-8 text-center">
                  <Mic2 className="w-10 h-10 text-white/20 mx-auto mb-3" />
                  <p className="text-white/60">Queue is empty</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingQueue.map((item, index) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="glass-card p-4"
                      data-testid={`admin-queue-item-${item.id}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center">
                          <span className="font-cinzel font-bold text-gold">{item.position}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-white">{item.user_name}</h3>
                          <p className="text-gold text-sm truncate">{item.song_title} - {item.artist}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleSetCurrent(item.id)}
                            data-testid={`set-current-${item.id}`}
                            className="bg-green-600 hover:bg-green-700 text-white"
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleRemoveFromQueue(item.id)}
                            data-testid={`remove-${item.id}`}
                          >
                            <XCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Users Management */}
          <TabsContent value="users" className="mt-6">
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10">
                <h2 className="font-cinzel font-bold text-lg text-white">All Users ({users.length})</h2>
              </div>
              <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
                {users.map((u, index) => (
                  <motion.div
                    key={u.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.02 }}
                    className="flex items-center gap-4 p-4"
                    data-testid={`admin-user-${u.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-white truncate">{u.display_name}</h3>
                        {u.is_admin && (
                          <span className="text-xs bg-gold/20 text-gold px-2 py-0.5 rounded-full flex items-center gap-1">
                            <Shield className="w-3 h-3" /> Admin
                          </span>
                        )}
                      </div>
                      <p className="text-white/40 text-sm truncate">{u.email}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-gold text-sm">{u.points} pts</span>
                        <span className="text-white/40 text-xs">{u.rank?.name}</span>
                        <span className="text-white/40 text-xs">{u.songs_performed} songs</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Points Adjustment */}
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAdjustPoints(u.id, -10)}
                          data-testid={`minus-points-${u.id}`}
                          className="h-8 w-8 p-0 border-white/20 text-white hover:bg-white/10"
                        >
                          <Minus className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAdjustPoints(u.id, 10)}
                          data-testid={`plus-points-${u.id}`}
                          className="h-8 w-8 p-0 border-white/20 text-white hover:bg-white/10"
                        >
                          <Plus className="w-3 h-3" />
                        </Button>
                      </div>
                      {/* Toggle Admin */}
                      {u.id !== user?.id && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleToggleAdmin(u.id)}
                          data-testid={`toggle-admin-${u.id}`}
                          className={`h-8 border-white/20 ${u.is_admin ? 'text-gold' : 'text-white/60'} hover:bg-white/10`}
                        >
                          <UserCheck className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default AdminPage;
