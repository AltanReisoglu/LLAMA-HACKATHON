from typing import Dict, List, Optional, Tuple, Any
import requests
import json
from langchain_ollama.llms import OllamaLLM

import os
from datetime import datetime
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

import time
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

class GitHubProfileAnalyzer:
    """GitHub profil analizi yapan AI agent - ChromaDB ile kurs önerileri"""
    
    def __init__(self, github_token: Optional[str] = None, model_name: str = "llama3.1:8b", 
                 chroma_path: str = "./chroma_db"):
        """
        Args:
            github_token: GitHub API token (opsiyonel, rate limit için önerilir)
            model_name: Ollama model adı (llama3.2, llama2, mistral vb.)
            chroma_path: ChromaDB veritabanı yolu
        """
        self.github_token = github_token
        self.headers = {"Authorization": f"token {github_token}"} if github_token else {}
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Ollama LLM'i başlat
        try:
            self.llm = OllamaLLM(model=model_name, temperature=0.7)
            print(f"✅ Ollama modeli '{model_name}' başarıyla yüklendi")
        except Exception as e:
            print(f"⚠️ Ollama bağlantı hatası: {e}")
            print("💡 Ollama'nın çalıştığından emin olun: 'ollama serve'")
            self.llm = None
        
        # ChromaDB ve embedding fonksiyonu başlat
        try:
            self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
                model_name="nomic-embed-text",  # Ollama'da bulunan model
                url="http://localhost:11434/api/embeddings"
            )
            
            # PersistentClient için path parametresi
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            # Koleksiyon adını tutarlı kullanıyoruz: "courses"
            collection_name = "courses"
            try:
                self.courses_collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_fn
                )
                print(f"✅ ChromaDB '{collection_name}' koleksiyonu yüklendi")
            except Exception:
                self.courses_collection = self.chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_fn
                )
                print(f"✅ ChromaDB '{collection_name}' koleksiyonu oluşturuldu")
                
        except Exception as e:
            print(f"⚠️ ChromaDB bağlantı hatası: {e}")
            print("💡 ChromaDB'nin doğru yüklendiğinden emin olun")
            self.courses_collection = None
        
    def _make_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[requests.Response]:
        """Retry mantığı ile güvenli istek"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                # Rate limit kontrolü
                if response.status_code == 403:
                    rate_limit = response.headers.get('X-RateLimit-Remaining', 'Bilinmiyor')
                    if rate_limit == '0':
                        reset_time = response.headers.get('X-RateLimit-Reset', 'Bilinmiyor')
                        print(f"⚠️ Rate limit aşıldı. Reset zamanı: {reset_time}")
                        print("💡 GitHub token kullanarak rate limit'i artırabilirsiniz")
                    return None
                
                if response.status_code == 200:
                    return response
                    
                print(f"⚠️ HTTP {response.status_code} hatası, deneme {attempt + 1}/{max_retries}")
                
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout hatası, deneme {attempt + 1}/{max_retries}")
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Bağlantı hatası, deneme {attempt + 1}/{max_retries}: {str(e)[:100]}")
            except Exception as e:
                print(f"❌ Beklenmeyen hata: {str(e)[:100]}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ {wait_time} saniye bekleniyor...")
                time.sleep(wait_time)
        
        return None
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """GitHub kullanıcı profilini çek"""
        url = f"{self.base_url}/users/{username}"
        response = self._make_request(url)
        
        if response is None or response.status_code != 200:
            print(f"❌ Kullanıcı profili alınamadı: {username}")
            return None
        
        return response.json()
    
    def get_user_repos(self, username: str, max_repos: int = 50) -> List[Dict]:
        """Kullanıcının repolarını çek"""
        url = f"{self.base_url}/users/{username}/repos"
        params = {"per_page": min(max_repos, 100), "sort": "updated"}
        response = self._make_request(url, params)
        
        if response is None:
            print("⚠️ Repolar alınamadı, boş liste döndürülüyor")
            return []
        
        return response.json()
    
    def get_repo_languages(self, username: str, repo_name: str) -> Dict:
        """Repo dillerini çek"""
        url = f"{self.base_url}/repos/{username}/{repo_name}/languages"
        response = self._make_request(url)
        
        if response is None:
            return {}
        
        return response.json()
    
    def analyze_profile_data(self, username: str) -> Optional[Dict]:
        """Profil verilerini topla ve analiz et"""
        print(f"\n {username} kullanıcısının profili analiz ediliyor...")
        
        # Profil bilgilerini çek
        profile = self.get_user_profile(username)
        if profile is None:
            return None
        
        print(f"✅ Profil bilgileri alındı")
        
        repos = self.get_user_repos(username, max_repos=30)
        print(f"✅ {len(repos)} repo bilgisi alındı")
        
        # İstatistikleri hesapla
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
        total_forks = sum(repo.get('forks_count', 0) for repo in repos)
        
        # Dilleri topla (rate limit için sınırlı sayıda)
        all_languages = {}
        print(f"📝 Dil analizi yapılıyor (ilk 10 repo)...")
        
        for i, repo in enumerate(repos[:10]):
            if not repo.get('fork', False):
                langs = self.get_repo_languages(username, repo['name'])
                for lang, bytes_count in langs.items():
                    all_languages[lang] = all_languages.get(lang, 0) + bytes_count
                time.sleep(0.5)  # Rate limit için
        
        # En çok kullanılan diller
        sorted_languages = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)
        top_languages = [lang for lang, _ in sorted_languages[:10]]
        
        # Aktif repo sayısı (son 6 ayda güncellenmiş)
        try:
            six_months_ago = datetime.now().timestamp() - (6 * 30 * 24 * 60 * 60)
            active_repos = []
            for r in repos:
                try:
                    updated = datetime.strptime(r['updated_at'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                    if updated > six_months_ago:
                        active_repos.append(r)
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Aktivite hesaplaması sırasında hata: {e}")
            active_repos = []
        
        analysis_data = {
            'username': username,
            'name': profile.get('name') or 'N/A',
            'bio': profile.get('bio') or 'Biyografi yok',
            'location': profile.get('location') or 'Belirtilmemiş',
            'company': profile.get('company') or 'Belirtilmemiş',
            'public_repos': profile.get('public_repos', 0),
            'followers': profile.get('followers', 0),
            'following': profile.get('following', 0),
            'account_created': profile.get('created_at', 'N/A'),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'top_languages': top_languages if top_languages else ['Veri yok'],
            'active_repos_count': len(active_repos),
            'top_repos': sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:5]
        }
        
        print(f"✅ Analiz tamamlandı\n")
        return analysis_data
    
    def calculate_score(self, data: Dict) -> Dict:
        """Profil skoru hesapla"""
        score_breakdown = {
            'repo_count': min((data['public_repos'] / 50) * 20, 20),
            'followers': min((data['followers'] / 100) * 15, 15),
            'stars': min((data['total_stars'] / 200) * 25, 25),
            'activity': min((data['active_repos_count'] / 10) * 15, 15),
            'language_diversity': min(len(data['top_languages']) * 2.5, 15),
            'forks': min((data['total_forks'] / 50) * 10, 10)
        }
        
        total_score = sum(score_breakdown.values())
        
        return {
            'total_score': round(total_score, 1),
            'max_score': 100,
            'breakdown': score_breakdown,
            'rating': self._get_rating(total_score)
        }
    
    def _get_rating(self, score: float) -> str:
        """Skor bazlı değerlendirme"""
        if score >= 80:
            return "⭐⭐⭐⭐⭐ Mükemmel"
        elif score >= 60:
            return "⭐⭐⭐⭐ Çok İyi"
        elif score >= 40:
            return "⭐⭐⭐ İyi"
        elif score >= 20:
            return "⭐⭐ Orta"
        else:
            return "⭐ Başlangıç"
    
    def retrieve_courses_from_chromadb(self, languages: List[str], level: str, n_results: int = 5) -> List[Dict]:
        """ChromaDB'den kullanıcı profiline uygun kursları retrieve et"""
        if self.courses_collection is None:
            print("⚠️ ChromaDB koleksiyonu mevcut değil")
            return []
        
        print(f"🔍 ChromaDB'den kurs aranıyor - Diller: {languages[:3]}")
        
        # Her dil için ayrı ayrı sorgu yap
        all_courses = []
        seen_course_names = set()  # Duplikasyon önlemek için
        
        for lang in languages[:5]:  # İlk 5 dili kullan
            try:
                result = self.courses_collection.query(
                    query_texts=[f"{lang} programming"],
                    n_results=n_results
                )
                
                # Sonuçları işle
                # result yapısı: {'ids': [[...]], 'distances': [[...]], 'documents': [[...]], 'metadatas': [[...]]}
                if result and result.get('documents') and result['documents'][0]:
                    docs = result['documents'][0]
                    metas = result.get('metadatas', [[]])[0]
                    dists = result.get('distances', [[]])[0]
                    for i in range(len(docs)):
                        meta = metas[i] if i < len(metas) else {}
                        course_name = meta.get('course_name') or meta.get('title') or docs[i][:80]
                        link = meta.get('link') or meta.get('url') or meta.get('source') or ''
                        
                        # Duplikasyonu önle
                        if course_name and course_name not in seen_course_names:
                            course_info = {
                                'content': docs[i],
                                'metadata': {
                                    **meta,
                                    'link': link
                                },
                                'distance': dists[i] if i < len(dists) else None,
                                'similarity': 1 - (dists[i] if i < len(dists) else 0),
                                'language_match': lang  # Hangi dil için bulundu
                            }
                            all_courses.append(course_info)
                            seen_course_names.add(course_name)
                            
            except Exception as e:
                print(f"⚠️ {lang} için sorgu hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala
        all_courses.sort(key=lambda x: x['similarity'] if x.get('similarity') is not None else 0, reverse=True)
        
        # En iyi n_results kadarını al
        top_courses = all_courses[:n_results * 2]  # Biraz fazla al, LLM seçsin
        
        if top_courses:
            print(f"✅ {len(top_courses)} benzersiz kurs bulundu")
            print(f"   En yüksek benzerlik: {top_courses[0]['similarity']:.2f}")
            print(f"   Bulunan diller: {set(c['language_match'] for c in top_courses)}")
        else:
            print("⚠️ Hiç kurs bulunamadı")
        
        return top_courses
            
        
    
    def generate_ai_analysis(self, data: Dict, score_data: Dict) -> str:
        """LLM ile detaylı analiz oluştur"""
        
        
        template = """Profesyonel bir GitHub profil yardımcısısın. Görevin, aşağıda sağlanan profil verilerini analiz etmek ve aşağıdaki yapıya bağlı kalarak Türkçe geri bildirim vermektir:

1. Güçlü Yönleri belirt.
2. Geliştirilebilecek Alanlardan bahset.
3. Pratik Öneriler sun.
4. Kariyer Tavsiyesi ver.

Profil Verileri:
{profile_data}

Puan Verileri:
{score_data}

İçten, motive edici ve yapıcı bir ton kullan. Yazarken kısa ve öz ol.
"""
        
        try:
            if self.llm is None:
                # Fallback kısa analiz
                return ("(LLM erişimi yok — hızlı özet) Güçlü yönler: açık bir repo aktivitesi, popüler repolar var. "
                        "Geliştir: README ve issue/PR etkinliğini arttır. Pratik: her projeye kısa demo ekle. Kariyer: "
                        "portfolyo sitesi yap.")
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            profile_summary = f"""Kullanıcı: {data['username']}, İsim: {data['name']}, Repo: {data['public_repos']}, Takipçi: {data['followers']}, Yıldız: {data['total_stars']}, Diller: {', '.join(data['top_languages'][:5])}"""
            
            score_summary = f"""Skor: {score_data['total_score']}/100, Seviye: {score_data['rating']}"""
            
            print("🤖 AI analizi oluşturuluyor...\n")
            ai_analysis = chain.invoke({"profile_data": profile_summary, "score_data": score_summary})
            
            return ai_analysis
            
        except Exception as e:
            print(f"⚠️ AI analizi oluşturulamadı: {e}")
            return "(AI analizi sırasında hata oluştu, lütfen loglara bakın.)"
    
    def generate_course_recommendations(self, data: Dict) -> Tuple[str, List[Dict], List[Dict]]:
        """ChromaDB'den retrieve edilen kurslarla öneriler oluştur
           Döner: (recommendations_text, retrieved_courses_list, two_courses_json_list)"""
        
        print("DATALARFA")
        print(data['top_languages'])
        # Seviye belirleme
        level = "Beginner" if data['public_repos'] < 10 else "Intermediate" if data['public_repos'] < 30 else "Advanced"
        
        # ChromaDB'den kurs retrieve et
        retrieved_courses = self.retrieve_courses_from_chromadb(
            languages=data['top_languages'][:5],
            level=level,
            n_results=5
        )
        
        # Eğer ChromaDB boşsa fallback kurslar kullan
        if not retrieved_courses:
            fallback_text = self._generate_fallback_courses(data)
            # İki fallback kursu JSON olarak hazırlamak için basit yapı
            fallback_courses_for_json = [
                {"course_name": data['top_languages'][0] + " Advanced Concepts (Udemy)", "link": "", "notes": "Fallback"},
                {"course_name": "System Design & Architecture (Coursera)", "link": "", "notes": "Fallback"}
            ]
            return fallback_text, [], fallback_courses_for_json
        
        # Retrieve edilen kursları formatlı string'e çevir
        courses_context = "\n\n".join([
            f"Kurs {i+1}:\n{course['content']}\nKurs Metadatası: {course['metadata']}\n(Benzerlik skoru: {course['similarity']:.2f})"
            for i, course in enumerate(retrieved_courses[:5])
        ])
        
        template = """Sen profesyonel bir kariyer danışmanı ve kurs tavsiye motorusun.

Aşağıda ChromaDB'den retrieve edilmiş, kullanıcının profiliyle ilgili kurslar var:

{courses_context}

Kullanıcının mevcut durumu:
- Diller: {languages}
- Seviye: {level}
- Repo sayısı: {repo_count}

Bu retrieve edilmiş kursları kullanarak, kullanıcıya EN UYGUN 5 KURSU seç ve öner.
Her kurs için şunları belirt:
- Kurs Adı ve Platform
- Neden Bu Kursu Öneriyorum (kullanıcının profiline göre)
- Tahmini Süre

Yanıt **kısa, açık ve tamamen Türkçe** olmalıdır.
"""
        
        # Eğer LLM yoksa kısa öneri metnini kendimiz hazırlayalım
        if self.llm is None:
            recommendations_text = "LLM erişimi yok — aşağıda ChromaDB'den eşleşen kurslar listelenmiştir:\n\n" + courses_context
            # JSON için ilk 2 course metadata'sını ayıkla
            two_courses_meta = []
            for c in retrieved_courses[:2]:
                meta = c.get('metadata', {})
                two_courses_meta.append({
                    "course_name": meta.get('course_name') or meta.get('title') or c['content'][:80],
                    "link": meta.get('link', ''),
                    "similarity": c.get('similarity')
                })
            return recommendations_text, retrieved_courses, two_courses_meta
        
        try:
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            print("📚 ChromaDB kursları kullanılarak öneriler hazırlanıyor...\n")
            recommendations = chain.invoke({
                "courses_context": courses_context,
                "languages": ', '.join(data['top_languages'][:8]),
                "level": level,
                "repo_count": data['public_repos']
            })
            
            # JSON'a konulacak ilk iki kursun metadata'sını hazırla
            two_courses_meta = []
            for c in retrieved_courses[:2]:
                meta = c.get('metadata', {})
                two_courses_meta.append({
                    "course_name": meta.get('course_name') or meta.get('title') or c['content'][:80],
                    "link": meta.get('link', ''),
                    "similarity": c.get('similarity'),
                    "language_match": c.get('language_match')
                })
            
            return recommendations, retrieved_courses, two_courses_meta
        
        except Exception as e:
            print(f"⚠️ Kurs önerileri oluşturulurken hata: {e}")
            # Fallback text but still return retrieved courses
            fallback_text = "Kurs önerileri oluşturulamadı (LLM hatası). Ancak ChromaDB sonuçları aşağıdadır:\n\n" + courses_context
            two_courses_meta = []
            for c in retrieved_courses[:2]:
                meta = c.get('metadata', {})
                two_courses_meta.append({
                    "course_name": meta.get('course_name') or meta.get('title') or c['content'][:80],
                    "link": meta.get('link', ''),
                    "similarity": c.get('similarity'),
                    "language_match": c.get('language_match')
                })
            return fallback_text, retrieved_courses, two_courses_meta
            
        
    def _generate_fallback_courses(self, data: Dict) -> str:
        """Temel kurs önerileri"""
        top_lang = data['top_languages'][0] if data['top_languages'] else 'Python'
        
        courses = f"""
### 📚 Önerilen Kurslar

1. **{top_lang} Advanced Concepts** (Udemy)
   - Derin {top_lang} bilgisi için
   - 30-40 saat
   - Link: (metadata yok)
   
2. **System Design & Architecture** (Coursera)
   - Büyük sistemler tasarla
   - 20-30 saat
   - Link: (metadata yok)
   
3. **Git & GitHub Mastery** (YouTube/FreeCodeCamp)
   - Version control uzmanlığı
   - 10-15 saat
   
4. **Clean Code Principles** (Udemy)
   - Kod kalitesini artır
   - 15-20 saat
   
5. **DevOps Fundamentals** (Pluralsight)
   - CI/CD ve deployment
   - 25-35 saat

💡 **Öneri:** Önce System Design, sonra DevOps, ardından diğerleri.
"""
        return courses
    
    def generate_full_report(self, username: str) -> Tuple[Any, Any, Any]:
        """Tam rapor oluştur
           Döndürür: (report_str, hw_courses_list, two_courses_json_str)
        """
        try:
            # Veri toplama
            data = self.analyze_profile_data(username)
            
            if data is None:
                return (f"❌ {username} kullanıcısı için profil verisi alınamadı.\n\n💡 Kontrol edin:\n- İnternet bağlantınız\n- Kullanıcı adı doğru mu\n- GitHub API erişilebilir mi", [], "[]")
            
            # Skor hesaplama
            score_data = self.calculate_score(data)
            
            # AI analizleri
            ai_analysis = self.generate_ai_analysis(data, score_data)
            course_recommendations, retrieved_courses, two_courses_meta = self.generate_course_recommendations(data)
            
            hw_courses = retrieved_courses[:2] if retrieved_courses else []
            # two_courses_meta already list of dicts for JSON
            
            # Raporu birleştir
            report = f"""
# 🎯 GitHub Profil Analiz Raporu

## 👤 Kullanıcı Bilgileri
- **Kullanıcı Adı:** {data['username']}
- **İsim:** {data['name']}
- **Biyografi:** {data['bio']}
- **Konum:** {data['location']}
- **Şirket:** {data['company']}
- **Hesap Oluşturma:** {data['account_created'][:10]}

## 📊 İstatistikler
- **Toplam Repo:** {data['public_repos']}
- **Takipçi:** {data['followers']}
- **Takip Edilen:** {data['following']}
- **Toplam Yıldız:** {data['total_stars']} ⭐
- **Toplam Fork:** {data['total_forks']} 🔱
- **Aktif Repo (Son 6 Ay):** {data['active_repos_count']}

## 💻 En Çok Kullanılan Diller
{', '.join(data['top_languages'])}

## 🏆 En Popüler Repolar
"""
            for i, repo in enumerate(data['top_repos'], 1):
                report += f"\n{i}. **{repo['name']}** - ⭐ {repo['stargazers_count']} | 🔱 {repo.get('forks_count', 0)}"
                if repo.get('description'):
                    report += f"\n   _{repo['description']}_"
                # Repo link ekle
                if repo.get('html_url'):
                    report += f"\n   Link: {repo.get('html_url')}"
                report += "\n"
            
            report += f"""
## 📈 Profil Skoru
**{score_data['total_score']}/{score_data['max_score']}** - {score_data['rating']}

### Detaylı Skor:
- 📦 Repo Sayısı: {score_data['breakdown']['repo_count']:.1f}/20
- 👥 Takipçi: {score_data['breakdown']['followers']:.1f}/15
- ⭐ Yıldız: {score_data['breakdown']['stars']:.1f}/25
- 🔄 Aktivite: {score_data['breakdown']['activity']:.1f}/15
- 💬 Dil Çeşitliliği: {score_data['breakdown']['language_diversity']:.1f}/15
- 🔱 Fork: {score_data['breakdown']['forks']:.1f}/10

## 🤖 AI Analizi
{ai_analysis}

## 📚 Öğrenme Yol Haritası (ChromaDB Retrieval)
{course_recommendations}

## 🔗 Kurs Metadataları (ilk 5'ten seçilenlerin linkleri)
"""
            # Ek olarak bulunan kursların metadata link'lerini listele
            if retrieved_courses:
                for i, c in enumerate(retrieved_courses[:5], 1):
                    meta = c.get('metadata', {})
                    course_name = meta.get('course_name') or meta.get('title') or c['content'][:60]
                    link = meta.get('link', '') or meta.get('url', '') or '(link yok)'
                    report += f"\n{i}. {course_name}\n   Link: {link}\n   Similarity: {c.get('similarity')}\n"
            else:
                report += "\nHiç kurs bulunamadı veya ChromaDB boş.\n"
            
            report += f"""
--- 
*Rapor: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Powered by ChromaDB + Ollama + GitHub API*
"""
            # two_courses_meta -> JSON string
            try:
                two_courses_json = json.dumps(two_courses_meta, ensure_ascii=False, indent=2)
            except Exception:
                two_courses_json = "[]"
            
            return report, hw_courses, two_courses_json
            
        except Exception as e:
            return (f"❌ Beklenmeyen hata: {str(e)}\n\nLütfen:\n1. İnternet bağlantısını kontrol edin\n2. Ollama'nın çalıştığından emin olun\n3. GitHub API'nin erişilebilir olduğunu doğrulayın\n4. ChromaDB'nin doğru yapılandırıldığını kontrol edin", [], "[]")

if __name__ == "__main__":
    analyzer = GitHubProfileAnalyzer(github_token="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")
    report, top_two_courses, two_courses_json = analyzer.generate_full_report("pdichone")
    import re

    def bolumlere_ayir(text):
        # Tüm ana başlıkları (## ...) bul
        basliklar = re.findall(r"^##\s+.*", text, re.MULTILINE)
        bolumler = {}
        
        for i, baslik in enumerate(basliklar):
            baslik_adi = baslik.replace("##", "").strip()
            start = text.find(baslik)
            end = text.find(basliklar[i + 1], start + 1) if i + 1 < len(basliklar) else len(text)
            bolumler[baslik_adi] = text[start:end].strip()
        
        return bolumler
    bolumler = bolumlere_ayir(report)
    print(bolumler.get("👤 Kullanıcı Bilgileri", "Kullanıcı bilgileri bulunamadı"))
        
                        
         