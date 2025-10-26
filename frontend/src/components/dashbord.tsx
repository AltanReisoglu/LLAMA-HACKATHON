import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Card, CardHeader, CardTitle, CardContent, CardDescription 
} from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { Plus, Trash2, Check, Target, Briefcase, BookOpen, Link, User } from 'lucide-react';

interface DashboardResponse {
  name: string;
  course_1: string;
  course_2: string;
  link_1?: string;
  link_2?: string;
  q1?: string;
  q2?: string;
}

interface Task {
  id: number;
  text: string;
  completed: boolean;
  category: string;
}

export default function CareerTodoList() {
  const [userData, setUserData] = useState<DashboardResponse | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Hazırlık');
  const [loading, setLoading] = useState(false);
  const [userLoading, setUserLoading] = useState(true);

  const categories = ['Hazırlık', 'Araştırma', 'Başvuru', 'Görüşme', 'Gelişim'];

  // Kullanıcı verilerini çek
  useEffect(() => {
    const fetchUserData = async () => {
      setUserLoading(true);
      try {
        const response = await axios.get('/userstats');
        setUserData(response.data);
        
        // Kullanıcı verilerine göre başlangıç görevleri oluştur
        const initialTasks: Task[] = [];
        
        if (response.data.course_1) {
          initialTasks.push({
            id: 1,
            text: `${response.data.course_1} kursunu tamamla`,
            completed: false,
            category: 'Gelişim'
          });
        }
        
        if (response.data.course_2) {
          initialTasks.push({
            id: 2,
            text: `${response.data.course_2} kursunu tamamla`,
            completed: false,
            category: 'Gelişim'
          });
        }
        
        if (response.data.q1) {
          initialTasks.push({
            id: 3,
            text: `Hedef: ${response.data.q1}`,
            completed: false,
            category: 'Hazırlık'
          });
        }
        
        if (response.data.q2) {
          initialTasks.push({
            id: 4,
            text: `Hedef: ${response.data.q2}`,
            completed: false,
            category: 'Hazırlık'
          });
        }
        
        setTasks(initialTasks);
      } catch (error) {
        console.error('Kullanıcı verileri alınamadı:', error);
      } finally {
        setUserLoading(false);
      }
    };

    fetchUserData();
  }, []);

  // Yeni görev ekle
  const addTask = async () => {
    if (!newTask.trim()) return;

    const newItem: Task = {
      id: Date.now(),
      text: newTask,
      completed: false,
      category: selectedCategory,
    };

    setTasks(prev => [...prev, newItem]);
    setNewTask('');
  };

  // Görev durumunu değiştir
  const toggleTask = (id: number) => {
    setTasks(prev => prev.map(task =>
      task.id === id ? { ...task, completed: !task.completed } : task
    ));
  };

  // Görev sil
  const deleteTask = (id: number) => {
    setTasks(prev => prev.filter(task => task.id !== id));
  };

  const completedCount = tasks.filter(t => t.completed).length;
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  if (userLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-500">Kullanıcı verileri yükleniyor...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Kullanıcı Bilgileri */}
      {userData && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-blue-600" />
              Hoş Geldin, {userData.name}
            </CardTitle>
            <CardDescription>Kariyer yolculuğun için öneriler</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Kurs 1 */}
              <div className="p-4 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  <h3 className="font-semibold text-gray-800">{userData.course_1}</h3>
                </div>
                {userData.link_1 && (
                  <a 
                    href={userData.link_1} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                  >
                    <Link className="h-3 w-3" />
                    Kurs Linki
                  </a>
                )}
                {userData.q1 && (
                  <p className="text-sm text-gray-600 mt-2">{userData.q1}</p>
                )}
              </div>

              {/* Kurs 2 */}
              <div className="p-4 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  <h3 className="font-semibold text-gray-800">{userData.course_2}</h3>
                </div>
                {userData.link_2 && (
                  <a 
                    href={userData.link_2} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                  >
                    <Link className="h-3 w-3" />
                    Kurs Linki
                  </a>
                )}
                {userData.q2 && (
                  <p className="text-sm text-gray-600 mt-2">{userData.q2}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Başlık */}
      <div>
        <h1 className="text-gray-900 mb-1 flex items-center gap-2">
          <Briefcase className="h-6 w-6 text-blue-600" />
          Kariyer Planlama Paneli
        </h1>
        <p className="text-gray-600">Hedeflerinizi yönetin ve ilerlemenizi takip edin</p>
      </div>

      {/* İlerleme Durumu */}
      <Card>
        <CardHeader>
          <CardTitle>İlerleme Durumu</CardTitle>
          <CardDescription>Tamamlanan görev yüzdesi</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between mb-2">
            <span className="text-gray-600">
              {completedCount} / {tasks.length} görev
            </span>
            <span className="text-gray-900 font-semibold">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
        </CardContent>
      </Card>

      {/* Görev Ekle */}
      <Card>
        <CardHeader>
          <CardTitle>Yeni Görev Ekle</CardTitle>
          <CardDescription>Kariyer hedeflerinizi ekleyin</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 mb-3">
            <Input
              placeholder="Yeni görev yaz..."
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addTask()}
            />
            <Button onClick={addTask} disabled={loading}>
              <Plus className="h-4 w-4 mr-2" /> Ekle
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <Button
                key={cat}
                variant={selectedCategory === cat ? 'default' : 'outline'}
                onClick={() => setSelectedCategory(cat)}
                className="rounded-full text-sm"
              >
                {cat}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Görev Listesi */}
      <Card>
        <CardHeader>
          <CardTitle>Görev Listesi</CardTitle>
          <CardDescription>Kategorilere göre düzenlenmiş</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-gray-500">Görevler yükleniyor...</p>
          ) : tasks.length === 0 ? (
            <div className="text-center py-10">
              <Target className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Henüz görev bulunmuyor.</p>
            </div>
          ) : (
            categories.map(category => {
              const categoryTasks = tasks.filter(t => t.category === category);
              if (categoryTasks.length === 0) return null;

              return (
                <div key={category} className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Target className="w-5 h-5 text-blue-600" /> {category}
                  </h3>
                  <div className="space-y-2">
                    {categoryTasks.map(task => (
                      <div
                        key={task.id}
                        className={`flex items-center gap-3 p-4 rounded-lg border transition-all ${
                          task.completed
                            ? 'bg-green-50 border-green-200'
                            : 'bg-white border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <button
                          onClick={() => toggleTask(task.id)}
                          className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                            task.completed
                              ? 'bg-green-500 border-green-500'
                              : 'border-gray-300 hover:border-blue-500'
                          }`}
                        >
                          {task.completed && <Check className="w-4 h-4 text-white" />}
                        </button>

                        <span
                          className={`flex-1 ${
                            task.completed ? 'line-through text-gray-500' : 'text-gray-800'
                          }`}
                        >
                          {task.text}
                        </span>

                        <Button
                          variant="ghost"
                          onClick={() => deleteTask(task.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-5 h-5" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
