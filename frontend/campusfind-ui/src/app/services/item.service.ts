
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ItemReport {
  id: number;
  title: string;
  description: string;
  item_type: 'lost' | 'found';
  category: string;
  location: string;
  event_date: string;
  image_url?: string | null;
  created_at?: string;
  owner_id?: number | null;
}

export interface SemanticMatchResponse {
  source_item_id: number;
  source_title: string;
  source_type: 'lost' | 'found';
  compared_against: 'lost' | 'found';
  total_matches: number;
  matches: SemanticMatch[];
}

export interface SemanticMatch extends ItemReport {
  similarity_score: number;
}

@Injectable({
  providedIn: 'root'
})
export class ItemService {

  private readonly http = inject(HttpClient);

  private readonly api = 'http://127.0.0.1:8000/items';

  // Get all reports - Public
  getAll(): Observable<ItemReport[]> {
    return this.http.get<ItemReport[]>(`${this.api}/`);
  }

  // Get reports belonging to the logged-in student
  getMyReports(): Observable<ItemReport[]> {
    return this.http.get<ItemReport[]>(
      `${this.api}/my-reports`
    );
  }

  // Search reports
  search(filters: Record<string, string>): Observable<ItemReport[]> {
    let params = new HttpParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params = params.set(key, value);
      }
    });

    return this.http.get<ItemReport[]>(
      `${this.api}/search`,
      { params }
    );
  }

  // Get individual report
  getById(id: number): Observable<ItemReport> {
    return this.http.get<ItemReport>(`${this.api}/${id}`);
  }

  // Find semantically similar reports using AI embeddings
  getSemanticMatches(
    id: number,
    limit: number = 10
  ): Observable<SemanticMatchResponse> {
    const params = new HttpParams().set('limit', limit);

    return this.http.get<SemanticMatchResponse>(
      `${this.api}/${id}/matches`,
      { params }
    );
  }

  // Create report
  create(item: Partial<ItemReport>): Observable<ItemReport> {
    return this.http.post<ItemReport>(`${this.api}/`, item);
  }

  // Update report
  update(id: number, item: Partial<ItemReport>): Observable<ItemReport> {
    return this.http.put<ItemReport>(`${this.api}/${id}`, item);
  }

  // Delete report
  delete(id: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.api}/${id}`);
  }

  // Upload or replace report image
  uploadImage(id: number, file: File): Observable<ItemReport> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<ItemReport>(
      `${this.api}/${id}/image`,
      formData
    );
  }
}
