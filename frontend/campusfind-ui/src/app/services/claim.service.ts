
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

// Claim response interface
export interface Claim {
  id: number;
  item_id: number;
  claimant_id: number;
  message: string;
  status: 'pending' | 'approved' | 'rejected';
  owner_response: string | null;
  created_at: string;
  updated_at: string | null;
}

// Request interface for submitting a claim
export interface ClaimCreate {
  item_id: number;
  message: string;
}

// Request interface for owner review
export interface ClaimReview {
  status: 'approved' | 'rejected';
  owner_response?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ClaimService {

  private readonly http = inject(HttpClient);

  private readonly api = `${environment.apiUrl}/claims`;

  // Submit a claim for a found item
  createClaim(data: ClaimCreate): Observable<Claim> {
    return this.http.post<Claim>(
      `${this.api}/`,
      data
    );
  }

  // Get claims submitted by the logged-in student
  getMyClaims(): Observable<Claim[]> {
    return this.http.get<Claim[]>(
      `${this.api}/my-claims`
    );
  }

  // Get claims received by the logged-in item owner
  getReceivedClaims(): Observable<Claim[]> {
    return this.http.get<Claim[]>(
      `${this.api}/received`
    );
  }

  // Approve or reject a claim
  reviewClaim(
    claimId: number,
    data: ClaimReview
  ): Observable<Claim> {
    return this.http.patch<Claim>(
      `${this.api}/${claimId}/review`,
      data
    );
  }
}
