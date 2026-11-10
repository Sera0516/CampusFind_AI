
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AssistantRequest {
  question: string;
}

export interface RetrievedReport {
  id?: number;
  title?: string;
  description?: string;
  item_type?: 'lost' | 'found';
  category?: string;
  location?: string;
  event_date?: string;
  similarity_score?: number;
  hybrid_score?: number;
  report_ids?: number[];
  duplicate_count?: number;
}

export interface AssistantResponse {
  question: string;
  answer: string;
  retrieved_reports: RetrievedReport[];
  total_retrieved: number;
}

@Injectable({
  providedIn: 'root'
})
export class AssistantService {

  private readonly http = inject(HttpClient);

  private readonly api = `${environment.apiUrl}/assistant`;

  // Ask the CampusFind AI RAG assistant
  ask(question: string): Observable<AssistantResponse> {
    return this.http.post<AssistantResponse>(
      `${this.api}/ask`,
      { question }
    );
  }
}
