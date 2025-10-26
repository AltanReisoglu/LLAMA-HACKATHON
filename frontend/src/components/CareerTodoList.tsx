import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { Plus, Trash2, Check, Target, Briefcase } from 'lucide-react';

// Mock API (örnek olarak JSONPlaceholder)
const API_URL = 'https://jsonplaceholder.typicode.com/todos';

interface Task {
  id: number;
  text: string;
  completed: boolean;
  category: string;
}

export default function CareerTodoList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Hazırlık');
  const [loading, setLoading] = useState(false);

  const categories = ['Hazırlık', 'Araştırma', 'Başvuru', 'Görüşme', 'Gelişim'];

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true);
      try {
        const response = await axios.get("/userstats", { params: { _limit: 5 } });
        const formatted = response.data.map((t: any) => ({
          id: t.id,
          text: t.title || `Görev ${t.id}`,
          completed: t.completed || false,
          category: categories[Math.floor(Math.random() * categories.length)],
        }));
        setTasks(formatted);
      } catch (error) {
        console.error('Görevler alınamadı:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  const addTask = async () => {
    if (!newTask.trim()) return;

    const newItem: Task = {
      id: Date.now(),
      text: newTask,
      completed: false,
      category: selectedCategory,
    };

    try {
      await axios.post(API_URL, newItem);
      setTasks(prev => [...prev, newItem]);
      setNewTask('');
    } catch (error) {
      console.error('Görev eklenemedi:', error);
    }
  };

  const toggleTask = async (id: number) => {
    const updated = tasks.map(task =>
      task.id === id ? { ...task, completed: !task.completed } : task
    );
    setTasks(updated);

    try {
      const toggled = updated.find(t => t.id === id);
      await axios.patch(`${API_URL}/${id}`, { completed: toggled?.completed });
    } catch (error) {
      console.error('Görev güncellenemedi:', error);
    }
  };

  const deleteTask = async (id: number) => {
    try {
      await axios.delete(`${API_URL}/${id}`);
      setTasks(prev => prev.filter(task => task.id !== id));
    } catch (error) {
      console.error('Görev silinemedi:', error);
    }
  };

  const completedCount = tasks.filter(t => t.completed).length;
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0;

  return (
    <div className="space-y-6 p-4 max-w-3xl mx-auto">
      <div>
        <h1 className="text-gray-900 mb-1 flex items-center gap-2 text-2xl font-semibold">
          <Briefcase className="h-6 w-6" /> Kariyer Planlama Paneli
        </h1>
        <p className="text-gray-600">Hedeflerinizi yönetin ve ilerlemenizi takip edin</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>İlerleme Durumu</CardTitle>
          <CardDescription>Tamamlanan görev yüzdesi</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between mb-2">
            <span className="text-gray-600">{completedCount} / {tasks.length} görev</span>
            <span className="text-gray-900 font-semibold">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
        </CardContent>
      </Card>

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
              onKeyDown={(e) => e.key === 'Enter' && addTask()}
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
                    <Target className="w-5 h-5" /> {category}
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
