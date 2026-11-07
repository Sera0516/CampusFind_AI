import { environment } from '../../environments/environment';

import {
  Component,
  OnInit,
  inject,
  ChangeDetectorRef
} from '@angular/core';

import {
  CommonModule,
  DatePipe,
  UpperCasePipe
} from '@angular/common';

import { FormsModule } from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  ItemService,
  ItemReport,
  SemanticMatch,
  SemanticMatchResponse
} from '../services/item.service';

import { ClaimService } from '../services/claim.service';

@Component({
  selector: 'app-item-details',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    UpperCasePipe,
    FormsModule
  ],
  templateUrl: './item-details.html',
  styleUrl: './item-details.css'
})
export class ItemDetails implements OnInit {

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly itemService = inject(ItemService);
  private readonly claimService = inject(ClaimService);
  private readonly cdr = inject(ChangeDetectorRef);

  item: ItemReport | null = null;
  matches: SemanticMatch[] = [];

  loading = true;
  matchingLoading = false;

  errorMessage = '';
  matchingError = '';

  // Claim form state
  showClaimForm = false;
  claimMessage = '';
  submittingClaim = false;
  claimSuccess = '';
  claimError = '';

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));

    if (!Number.isInteger(id) || id <= 0) {
      this.loading = false;
      this.errorMessage = 'Invalid item ID.';
      this.cdr.markForCheck();
      return;
    }

    this.loadItem(id);
    this.loadMatches(id);
  }

  loadItem(id: number): void {
    this.loading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();

    this.itemService.getById(id).subscribe({

      next: (response) => {
        this.item = response;
        this.loading = false;
        this.cdr.markForCheck();

        console.log('Item details loaded:', response);
      },

      error: (error) => {
        console.error('Unable to load item:', error);

        this.errorMessage =
          error.status === 404
            ? 'This item report could not be found.'
            : 'Unable to load item details. Please try again.';

        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadMatches(id: number): void {
    this.matchingLoading = true;
    this.matchingError = '';
    this.cdr.markForCheck();

    this.itemService.getSemanticMatches(id, 10).subscribe({

      next: (response: SemanticMatchResponse) => {
        this.matches = response.matches;
        this.matchingLoading = false;
        this.cdr.markForCheck();
      },

      error: (error) => {
        console.error('Unable to load AI matches:', error);

        this.matchingError =
          'AI matches are currently unavailable.';

        this.matchingLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  openClaimForm(): void {
    this.showClaimForm = true;
    this.claimSuccess = '';
    this.claimError = '';
    this.cdr.markForCheck();
  }

  cancelClaim(): void {
    this.showClaimForm = false;
    this.claimMessage = '';
    this.claimError = '';
    this.cdr.markForCheck();
  }

  submitClaim(): void {
    if (!this.item) {
      return;
    }

    const message = this.claimMessage.trim();

    if (message.length < 10) {
      this.claimError =
        'Please provide at least 10 characters explaining your claim.';
      return;
    }

    this.submittingClaim = true;
    this.claimError = '';
    this.claimSuccess = '';
    this.cdr.markForCheck();

    this.claimService.createClaim({
      item_id: this.item.id,
      message: message
    }).subscribe({

      next: (response) => {
        this.submittingClaim = false;
        this.showClaimForm = false;
        this.claimMessage = '';

        this.claimSuccess =
          `Your claim #${response.id} has been submitted successfully. Its current status is ${response.status}.`;

        this.cdr.markForCheck();
      },

      error: (error) => {
        console.error('Unable to submit claim:', error);

        this.submittingClaim = false;

        this.claimError =
          error.error?.detail ||
          'Unable to submit your claim. Please try again.';

        this.cdr.markForCheck();
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  getImageUrl(imageUrl?: string | null): string {
    if (!imageUrl) {
      return '';
    }

    if (imageUrl.startsWith('http')) {
      return imageUrl;
    }

    return `${environment.apiUrl}${imageUrl}`;
  }
}

