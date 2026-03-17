import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, Users, Mic2, CheckCircle, XCircle, Play, 
  Plus, Minus, Crown, RefreshCw, UserCheck, Star, Gift, Search,
  Swords, Vote, Trophy, Trash2, AlertTriangle
} from 'lucide-react';
import { Layout } from '@/components/Layout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPage = () => {
  const { user } = useAuth();
  const [queue, setQueue] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [pointActions, setPointActions] = useState([]);
  const [activeBattles, setActiveBattles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [awardDialogOpen, setAwardDialogOpen] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);

  const fetchData = async () => {
    try {
      const [queueRes, usersRes, statsRes, actionsRes, battlesRes] = await Promise.all([
        axios.get(`${API}/queue`),
        axios.get(`${API}/admin/users`),
        axios.get(`${API}/stats`),
        axios.get(`${API}/point-actions`),
        axios.get(`${API}/challenges`)
      ]);
      setQueue(queueRes.data);
      setUsers(usersRes.data);
      setStats(statsRes.data);
      setPointActions(actionsRes.data);
      setActiveBattles(battlesRes.data.filter(b => b.status === 'accepted'));
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

  const handleAwardAction = async (actionId) => {
    if (!selectedUser) return;
    
    try {
      const response = await axios.post(`${API}/admin/award-points`, {
        user_id: selectedUser.id,
        action_id: actionId
      });
      
      const data = response.data;
      let message = `Awarded ${data.points_awarded} points to ${selectedUser.display_name}`;
      if (data.badges_earned?.length > 0) {
        message += ` + ${data.badges_earned.length} badge(s)!`;
      }
      toast.success(message);
      setAwardDialogOpen(false);
      setSelectedUser(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to award points');
    }
  };

  const openAwardDialog = (u) => {
    setSelectedUser(u);
    setAwardDialogOpen(true);
  };

  const openDeleteDialog = (u) => {
    setUserToDelete(u);
    setDeleteDialogOpen(true);
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    
    try {
      const response = await axios.delete(`${API}/admin/users/${userToDelete.id}`);
      toast.success(response.data.message);
      setDeleteDialogOpen(false);
      setUserToDelete(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  // Battle management functions
  const handleOpenVoting = async (challengeId) => {
    try {
      await axios.post(`${API}/challenges/${challengeId}/open-voting`);
      toast.success('Voting opened! All users notified.');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to open voting');
    }
  };

  const handleCloseVoting = async (challengeId) => {
    try {
      await axios.post(`${API}/challenges/${challengeId}/close-voting`);
      toast.success('Voting closed');
      fetchData();
    } catch (error) {
      toast.error('Failed to close voting');
    }
  };

  const handleFinalizeBattle = async (challengeId) => {
    try {
      const response = await axios.post(`${API}/challenges/${challengeId}/finalize`);
      toast.success(`${response.data.winner_name} wins the battle!`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to finalize battle');
    }
  };

  const handleCancelBattle = async (challengeId, winnerId) => {
    try {
      const response = await axios.post(`${API}/challenges/${challengeId}/cancel?winner_id=${winnerId}`);
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to decide winner');
    }
  };

  const currentSong = queue.find(item => item.status === 'current');
  const pendingQueue = queue.filter(item => item.status === 'pending');
  
  const filteredUsers = users.filter(u => 
    u.display_name.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.email.toLowerCase().includes(userSearch.toLowerCase())
  );

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
            <p className="text-white/60">Manage queue, users, and award points</p>
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
            <TabsTrigger 
              value="award"
              data-testid="award-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Gift className="w-4 h-4 mr-2" />
              Award Points
            </TabsTrigger>
            <TabsTrigger 
              value="battles"
              data-testid="battles-tab"
              className="data-[state=active]:bg-gold/20 data-[state=active]:text-gold"
            >
              <Swords className="w-4 h-4 mr-2" />
              Battles ({activeBattles.length})
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
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="p-3 bg-gold/10 rounded-xl shrink-0">
                      <Mic2 className="w-6 h-6 text-gold" />
                    </div>
                    <div className="min-w-0 overflow-hidden">
                      <h3 className="font-cinzel font-bold text-xl text-white truncate">{currentSong.user_name}</h3>
                      <p className="text-gold truncate">{currentSong.song_title} - {currentSong.artist}</p>
                      {currentSong.message_to_admin && (
                        <div className="mt-2 p-2 bg-purple-500/10 border border-purple-500/30 rounded-lg max-w-full overflow-hidden">
                          <p className="text-purple-300 text-xs font-medium mb-1">Message:</p>
                          <p className="text-white/80 text-sm break-words whitespace-pre-wrap">{currentSong.message_to_admin}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  <Button
                    onClick={() => handleCompleteSong(currentSong.id)}
                    data-testid="complete-song-btn"
                    className="btn-gold shrink-0"
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
                        <div className="flex-1 min-w-0 overflow-hidden">
                          <h3 className="font-medium text-white truncate">{item.user_name}</h3>
                          <p className="text-gold text-sm truncate">{item.song_title} - {item.artist}</p>
                          {item.message_to_admin && (
                            <div className="mt-2 p-2 bg-purple-500/10 border border-purple-500/30 rounded-lg max-w-full overflow-hidden">
                              <p className="text-purple-300 text-xs font-medium mb-1">Message from singer:</p>
                              <p className="text-white/80 text-sm break-words whitespace-pre-wrap">{item.message_to_admin}</p>
                            </div>
                          )}
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
                      {/* Delete User */}
                      {u.id !== user?.id && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openDeleteDialog(u)}
                          data-testid={`delete-user-${u.id}`}
                          className="h-8 w-8 p-0 border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                          title="Delete user"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Award Points Tab */}
          <TabsContent value="award" className="mt-6 space-y-6">
            {/* User Search */}
            <div className="glass-card p-4">
              <label className="block text-sm font-medium text-white/80 mb-2">Search User to Award Points</label>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                <input
                  type="text"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Search by name or email..."
                  data-testid="user-search-input"
                  className="w-full royal-input pl-12"
                />
              </div>
            </div>

            {/* User List for Award */}
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10 bg-gold/5">
                <h2 className="font-cinzel font-bold text-lg text-gold">Select User to Award Points</h2>
              </div>
              <div className="divide-y divide-white/5 max-h-[400px] overflow-y-auto">
                {filteredUsers.map((u, index) => (
                  <motion.div
                    key={u.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.02 }}
                    className="flex items-center justify-between p-4 hover:bg-white/5 cursor-pointer transition-colors"
                    onClick={() => openAwardDialog(u)}
                    data-testid={`award-user-${u.id}`}
                  >
                    <div>
                      <h3 className="font-medium text-white">{u.display_name}</h3>
                      <p className="text-white/40 text-sm">{u.points} points · {u.rank?.name}</p>
                    </div>
                    <Button size="sm" className="btn-gold">
                      <Gift className="w-4 h-4 mr-2" />
                      Award
                    </Button>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Point Actions Reference */}
            <div className="glass-card overflow-hidden">
              <div className="p-4 border-b border-white/10">
                <h2 className="font-cinzel font-bold text-lg text-white">Point Actions Reference</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-white/5">
                {pointActions.map((action) => (
                  <div key={action.id} className="p-4 bg-royal-paper">
                    <div className="flex items-center justify-between">
                      <span className="text-white">{action.name}</span>
                      <span className={`font-bold ${
                        action.points >= 100 ? 'text-gold' : 
                        action.points >= 50 ? 'text-purple-400' : 'text-white/80'
                      }`}>
                        +{action.points}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Battles Management */}
          <TabsContent value="battles" className="mt-6 space-y-6">
            {activeBattles.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <Swords className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60 text-lg">No active battles</p>
                <p className="text-white/40">Battles will appear here when users challenge each other</p>
              </div>
            ) : (
              <div className="space-y-4">
                {activeBattles.map((battle) => (
                  <motion.div
                    key={battle.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`glass-card p-6 ${battle.voting_open ? 'border-green-500/50' : 'border-white/10'}`}
                    data-testid={`admin-battle-${battle.id}`}
                  >
                    {/* Status Badge */}
                    {battle.voting_open && (
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-sm font-medium text-green-400 uppercase tracking-wider">Voting Open</span>
                      </div>
                    )}

                    {/* Battle Info */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className="p-3 bg-gold/10 rounded-xl">
                          <Swords className="w-6 h-6 text-gold" />
                        </div>
                        <div>
                          <p className="text-white/60 text-sm">{battle.type_info?.name}</p>
                          <h3 className="font-cinzel font-bold text-lg text-white">
                            {battle.challenger?.display_name} <span className="text-gold">vs</span> {battle.opponent?.display_name}
                          </h3>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white/60 text-sm">Votes</p>
                        <p className="text-gold font-bold text-xl">{battle.vote_count || 0}</p>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col gap-3">
                      <div className="flex gap-3">
                        {!battle.voting_open ? (
                          <Button
                            onClick={() => handleOpenVoting(battle.id)}
                            className="flex-1 bg-green-600 hover:bg-green-700"
                            data-testid={`open-voting-${battle.id}`}
                          >
                            <Vote className="w-4 h-4 mr-2" />
                            Open Voting
                          </Button>
                        ) : (
                          <Button
                            onClick={() => handleCloseVoting(battle.id)}
                            className="flex-1 bg-orange-600 hover:bg-orange-700"
                            data-testid={`close-voting-${battle.id}`}
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Close Voting
                          </Button>
                        )}
                        <Button
                          onClick={() => handleFinalizeBattle(battle.id)}
                          className="flex-1 btn-gold"
                          disabled={!battle.vote_count || battle.vote_count === 0}
                          data-testid={`finalize-${battle.id}`}
                        >
                          <Trophy className="w-4 h-4 mr-2" />
                          Finalize (By Votes)
                        </Button>
                      </div>
                      
                      {/* Admin Decide Winner - shown when no votes */}
                      <div className="border-t border-white/10 pt-3">
                        <p className="text-white/50 text-xs mb-2 text-center">Admin Pick Winner (No Votes Required)</p>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleCancelBattle(battle.id, battle.challenger_id)}
                            variant="outline"
                            className="flex-1 border-blue-500/50 text-blue-400 hover:bg-blue-500/20 hover:text-blue-300"
                            data-testid={`pick-challenger-${battle.id}`}
                          >
                            <Crown className="w-4 h-4 mr-1" />
                            {battle.challenger?.display_name} Wins
                          </Button>
                          <Button
                            onClick={() => handleCancelBattle(battle.id, battle.opponent_id)}
                            variant="outline"
                            className="flex-1 border-purple-500/50 text-purple-400 hover:bg-purple-500/20 hover:text-purple-300"
                            data-testid={`pick-opponent-${battle.id}`}
                          >
                            <Crown className="w-4 h-4 mr-1" />
                            {battle.opponent?.display_name} Wins
                          </Button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Award Points Dialog */}
      <Dialog open={awardDialogOpen} onOpenChange={setAwardDialogOpen}>
        <DialogContent className="bg-royal-paper border-white/10 text-white max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-cinzel text-2xl text-gold">
              Award Points to {selectedUser?.display_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2 mt-4">
            {pointActions.map((action) => (
              <button
                key={action.id}
                onClick={() => handleAwardAction(action.id)}
                data-testid={`award-action-${action.id}`}
                className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-gold/10 rounded-lg transition-colors text-left"
              >
                <div>
                  <p className="text-white font-medium">{action.name}</p>
                  <p className="text-white/50 text-sm">{action.description}</p>
                </div>
                <span className={`font-cinzel font-bold text-lg ${
                  action.points >= 100 ? 'text-gold' : 
                  action.points >= 50 ? 'text-purple-400' : 'text-white'
                }`}>
                  +{action.points}
                </span>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete User Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="bg-purple-deep border-white/10 max-w-md">
          <DialogHeader>
            <DialogTitle className="font-cinzel text-xl text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-6 h-6" />
              Delete User
            </DialogTitle>
            <DialogDescription className="text-white/70">
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {userToDelete && (
            <div className="py-4">
              <p className="text-white mb-2">
                Are you sure you want to delete <span className="font-bold text-gold">{userToDelete.display_name}</span>?
              </p>
              <p className="text-white/50 text-sm">
                This will permanently remove:
              </p>
              <ul className="text-white/50 text-sm list-disc list-inside mt-2">
                <li>Their account and profile</li>
                <li>All queue entries</li>
                <li>Check-in history</li>
                <li>Badges and accomplishments</li>
                <li>Battle history</li>
              </ul>
            </div>
          )}
          
          <DialogFooter className="gap-3">
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              className="border-white/20 text-white hover:bg-white/10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDeleteUser}
              className="bg-red-600 hover:bg-red-700 text-white"
              data-testid="confirm-delete-btn"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
};

export default AdminPage;
