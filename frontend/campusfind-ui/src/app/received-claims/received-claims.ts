
import {
  Component,
  OnInit,
  inject,
  ChangeDetectorRef
} from '@angular/core';

import {
  CommonModule,
  DatePipe,
  TitleCasePipe
} from '@angular/common';

import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';

import {
  ClaimService,
  Claim,
  ClaimReview
} from '../services/claim.service';

import {
  ItemService,
  ItemReport
} from '../services/item.service';

interface ReceivedClaim extends Claim {
  item?: ItemReport;
}

@Component({
  selector: 'app-received-claims',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    TitleCasePipe,
    FormsModule
  ],
  templateUrl: './received-claims.html',
  styleUrl: './received-claims.css'
})
export class ReceivedClaims implements OnInit {

  private readonly claimService = inject(ClaimService);
  private readonly itemService = inject(ItemService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly cdr = inject(ChangeDetectorRef);

  claims: ReceivedClaim[] = [];

  loading = true;
  errorMessage = '';

  reviewingClaimId: number | null = null;
  ownerResponses: Record<number, string> = {};

  successMessage = '';
  reviewError = '';

  selectedClaimId: number | null = null;

  ngOnInit(): void {
    const claimId = Number(
      this.route.snapshot.queryParamMap.get('claimId')
    );

    this.selectedClaimId =
      Number.isInteger(claimId) && claimId > 0
        ? claimId
        : null;

    this.loadReceivedClaims();
  }

  loadReceivedClaims(): void {
    this.loading = true;
    this.errorMessage = '';

    this.claimService.getReceivedClaims().subscribe({

      next: (response) => {
        this.claims = response;

        this.claims.forEach((claim) => {
          this.itemService.getById(claim.item_id).subscribe({

            next: (item) => {
              claim.item = item;
              this.cdr.markForCheck();
            },

            error: (error) => {
              console.error(
                `Unable to load item ${claim.item_id}:`,
                error
              );
            }

          });
        });

        this.loading = false;
        this.cdr.markForCheck();

        this.scrollToSelectedClaim();
      },

      error: (error) => {
        console.error('Unable to load received claims:', error);

        this.errorMessage =
          error.status === 401
            ? 'Please log in to view received claims.'
            : 'Unable to load received claims. Please try again.';

        this.loading = false;
        this.cdr.markForCheck();
      }

    });
  }

  private scrollToSelectedClaim(): void {
    if (this.selectedClaimId === null) {
      return;
    }

    setTimeout(() => {
      const element = document.getElementById(
        `claim-${this.selectedClaimId}`
      );

      element?.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }, 300);
  }

  reviewClaim(claim: ReceivedClaim, status: 'approved' | 'rejected'): void {

    if (claim.status !== 'pending') {
      return;
    }

    this.reviewingClaimId = claim.id;
    this.reviewError = '';
    this.successMessage = '';

    const reviewData: ClaimReview = {
      status,
      owner_response: this.ownerResponses[claim.id]?.trim() || null
    };

    this.claimService.reviewClaim(claim.id, reviewData).subscribe({

      next: (updatedClaim) => {

        const index = this.claims.findIndex(
          existing => existing.id === updatedClaim.id
        );

        if (index !== -1) {
          this.claims[index] = {
            ...this.claims[index],
            ...updatedClaim
          };
        }

        this.reviewingClaimId = null;

        this.successMessage =
          `Claim #${updatedClaim.id} has been ${status}.`;

        this.cdr.markForCheck();
      },

      error: (error) => {
        console.error('Unable to review claim:', error);

        this.reviewingClaimId = null;

        this.reviewError =
          error.error?.detail ||
          'Unable to process this claim. Please try again.';

        this.cdr.markForCheck();
      }

    });
  }

  getStatusClass(status: string): string {
    return `status-${status.toLowerCase()}`;
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  viewItem(itemId: number): void {
    this.router.navigate(['/item', itemId]);
  }
}
