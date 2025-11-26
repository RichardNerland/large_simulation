import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import itertools

class Year:
    """
    Class for tracking economic parameters for each simulation year.
    """
    def __init__(self, initial_inflation_rate, initial_unemployment_rate, 
                 initial_isa_cap, initial_isa_threshold, num_years):
        self.year_count = 1
        self.inflation_rate = initial_inflation_rate
        self.stable_inflation_rate = initial_inflation_rate
        self.unemployment_rate = initial_unemployment_rate
        self.stable_unemployment_rate = initial_unemployment_rate
        self.isa_cap = initial_isa_cap
        self.isa_threshold = initial_isa_threshold
        self.deflator = 1

    def next_year(self):
        """Advance to the next year and update economic conditions"""
        self.year_count = self.year_count + 1
        self.inflation_rate = self.stable_inflation_rate * .45 + self.inflation_rate * .5 + np.random.normal(0, .01)
        
        # Lognormal unemployment shock with proper scaling
        # Use mu and sigma parameters that keep most values in a reasonable range
        # mu = -4 and sigma = 0.5 gives a distribution centered around 0.018 with 95% of values below 0.05
        unemployment_shock = np.random.lognormal(-4, 0.5) 
        
        # Calculate new rate with more weight on stable rate for stability
        self.unemployment_rate = max(0.02, min(0.15,  # Keep between 2% and 15%
            self.stable_unemployment_rate * 0.7 + self.unemployment_rate * 0.2 + unemployment_shock))
        
        self.isa_cap = self.isa_cap * (1 + self.inflation_rate)
        self.isa_threshold = self.isa_threshold * (1 + self.inflation_rate)
        self.deflator = self.deflator * (1 + self.inflation_rate)

class Degree:
    """
    Class representing different degree options with associated parameters.
    """
    def __init__(self, name, mean_earnings, stdev, experience_growth, years_to_complete, home_prob):
        self.name = name
        self.mean_earnings = mean_earnings
        self.stdev = stdev
        self.experience_growth = experience_growth
        self.years_to_complete = years_to_complete
        self.home_prob = home_prob

@dataclass
class CounterfactualParams:
    """Parameters for counterfactual earnings and remittances"""
    base_earnings: float  # Base annual earnings per earner without education (default $1,503)
    earnings_growth: float  # Annual growth rate of earnings
    remittance_rate: float  # Percentage of income sent as remittances
    employment_rate: float  # Baseline employment rate
    # Household structure parameters
    household_size_counterfactual: int = 5  # HH size including control (5 members)
    household_size_remittance: int = 4  # HH size for remittance recipients (treated in Germany, so 4 members)
    num_earners: int = 2  # Number of earners in household
    control_earner_multiplier: float = 1.0  # Multiplier for control earner's income vs other earner(s)
    # Treatment effect for returners (GiveWell analysis: $4000 for Uganda returners)
    returner_treatment_effect: float = 0.0  # Additional annual income for those who return home after graduating

@dataclass
class ImpactParams:
    """Parameters for measuring social impact"""
    discount_rate: float  # Annual discount rate for utility calculations
    counterfactual: CounterfactualParams
    ppp_multiplier: float = 0.4  # Purchasing power parity multiplier for German to Ugandan earnings
    health_benefit_per_euro: float = 0.00003  # Health utility gained per euro of additional income (based on GiveWell's approach)
    migration_influence_factor: float = 0.05  # Additional people who migrate due to observing success
    moral_weight: float = 1.44  # Moral weight (alpha) for direct income effects, based on GiveWell's approach
    eur_to_usd: float = 0.8458  # Exchange rate: USD per EUR (GiveWell analysis). EUR earnings × this = USD equivalent

def calculate_utility(income: float) -> float:
    """Calculate log utility for a given income level."""
    return np.log(max(1, income))

# Simplified degree parameters
@dataclass
class DegreeParams:
    """Simplified parameters for a degree program"""
    name: str
    initial_salary: float  # Starting salary upon graduation
    salary_std: float  # Standard deviation of initial salary
    annual_growth: float  # Simple annual growth rate
    years_to_complete: int
    home_prob: float
    max_salary_multiplier: float = 1.5  # Cap earnings at this multiple of initial salary

class Student:
    """
    Simplified student class that tracks career progression and earnings
    """
    def __init__(self, degree: Degree, num_years: int, 
                 counterfactual_params: CounterfactualParams,
                 starting_age: int = 22, life_expectancy: float = 81.4,
                 stipend_income: float = 0, stipend_std: float = 0,
                 german_learning_years: int = 0, study_income: float = 0):
        """Initialize a student with the given degree parameters.
        
        Args:
            german_learning_years: Years spent learning German before traveling to Germany (0 for Uganda, 1 for Kenya/Rwanda)
            study_income: Income earned while studying in Germany after passing German (€14k for Kenya/Rwanda)
        """
        self.degree = degree
        self.num_years = num_years
        self.counterfactual_params = counterfactual_params
        
        # Pre-graduation stipend (side job + stipend income while studying) - for Uganda
        self.stipend_income = stipend_income
        self.stipend_std = stipend_std
        
        # German learning phase (for Kenya/Rwanda programs)
        self.german_learning_years = german_learning_years
        self.study_income = study_income  # €14k during studies in Germany
        self.passed_german = None  # None = not checked yet, True/False = result
        self.in_germany = german_learning_years == 0  # Uganda students start in Germany
        
        # Age tracking
        self.starting_age = starting_age
        self.life_expectancy = life_expectancy
        self.current_age = starting_age
        
        # Career tracking
        self.years_experience = 0
        self.earnings_power = 0
        self.is_graduated = False
        self.is_employed = False
        self.is_home = False
        
        # Calculate actual years to graduate with potential delay
        self.actual_years_to_complete = _calculate_graduation_delay(
            degree.years_to_complete, degree.name
        )
        
        # Payment tracking
        self.earnings = np.zeros(num_years)
        self.counterfactual_earnings = np.zeros(num_years)
        self.payments = np.zeros(num_years)
        self.real_payments = np.zeros(num_years)
        self.years_paid = 0
        self.hit_cap = False
        
        # Employment tracking
        self.employment_history = np.zeros(num_years, dtype=bool)
        self.unemployment_spells = []
        self.current_unemployment_spell = 0
        
        # Determine if student returns home after graduation
        self.will_return_home = np.random.random() < degree.home_prob
        
        # Track peak earnings
        self.peak_earnings = 0
        self.peak_earnings_age = 0
        
        # Add missing attributes
        self.id = None
        self.start_year = 0

    def has_graduated(self, relative_year: int) -> bool:
        """Check if the student has graduated by the given year.
        
        For Kenya/Rwanda programs, this accounts for the German learning year.
        """
        return relative_year >= self.german_learning_years + self.actual_years_to_complete

    def calculate_earnings(self, relative_year: int, year: Year) -> float:
        """
        Calculate earnings for the given year, considering graduation status,
        employment, and career progression.
        
        For Kenya/Rwanda programs:
        - Year 0: German learning phase, earn counterfactual income
        - German acquisition check at end of learning phase
        - If pass: travel to Germany, earn study_income (€14k) during studies
        - If fail: stay home, earn counterfactual forever
        - After graduation: earn degree earnings
        """
        # Update current age
        self.current_age = self.starting_age + relative_year
        
        # If past life expectancy, no earnings
        if self.current_age >= self.life_expectancy:
            return 0
        
        # German learning phase (Year 0 for Kenya/Rwanda)
        if relative_year < self.german_learning_years:
            # During German learning, earn counterfactual income in home country
            return self.calculate_counterfactual_earnings(relative_year, year)
        
        # Check German acquisition at end of learning phase (only once)
        if self.german_learning_years > 0 and self.passed_german is None:
            # NA students always fail German acquisition
            if self.degree.name == 'NA':
                self.passed_german = False
            else:
                # Non-NA students pass German and travel to Germany
                self.passed_german = True
            
            self.in_germany = self.passed_german
            
            # If failed German, they stay in home country
            if not self.passed_german:
                self.will_return_home = True
                self.is_home = True
        
        # If not in Germany (failed German), earn counterfactual forever
        if self.german_learning_years > 0 and not self.in_germany:
            return self.calculate_counterfactual_earnings(relative_year, year)
        
        # Check if student has graduated (accounting for German learning time)
        self.is_graduated = self.has_graduated(relative_year)
        
        # If not graduated, return study income or stipend
        if not self.is_graduated:
            # Kenya/Rwanda: €14k during studies in Germany
            if self.german_learning_years > 0 and self.study_income > 0:
                return self.study_income * year.deflator
            # Uganda: stipend income (side job + stipend while studying)
            elif self.stipend_income and self.stipend_income > 0:
                return max(0, np.random.normal(self.stipend_income, self.stipend_std) * year.deflator)
            return 0
            
        # Check if student has returned home after graduation
        # They earn counterfactual + treatment effect (if any)
        if self.will_return_home and relative_year >= self.german_learning_years + self.actual_years_to_complete:
            self.is_home = True
            # Use counterfactual earnings + treatment effect for home returns
            base_earnings = self.calculate_counterfactual_earnings(relative_year, year)
            # Add treatment effect (e.g., $4000 for Uganda returners per GiveWell analysis)
            # Treatment effect is per-person consumption increase, divided by HH size
            treatment_effect = self.counterfactual_params.returner_treatment_effect
            if treatment_effect > 0:
                hh_size = self.counterfactual_params.household_size_counterfactual
                per_person_treatment = treatment_effect / hh_size
                return base_earnings + per_person_treatment * year.deflator
            return base_earnings
        
        # Check employment status
        if year.unemployment_rate < 1:
            prev_employed = self.is_employed
            self.is_employed = np.random.binomial(1, 1 - year.unemployment_rate) == 1
            
            # Track unemployment spells
            if prev_employed and not self.is_employed:
                # Start of unemployment spell
                self.current_unemployment_spell = 1
            elif not prev_employed and not self.is_employed:
                # Continuing unemployment
                self.current_unemployment_spell += 1
            elif not prev_employed and self.is_employed:
                # End of unemployment spell
                if self.current_unemployment_spell > 0:
                    self.unemployment_spells.append(self.current_unemployment_spell)
                self.current_unemployment_spell = 0
        else:
            self.is_employed = False
            self.current_unemployment_spell += 1
        
        # Record employment status
        self.employment_history[relative_year] = self.is_employed
        
        # If not employed, no earnings
        if not self.is_employed:
            return 0
        
        # If just graduated or earnings power not set yet, set initial earnings power
        if relative_year == self.actual_years_to_complete or self.earnings_power == 0:
            # Adjust initial salary for inflation at time of graduation
            initial_salary = self.degree.mean_earnings * year.deflator
            salary_std = self.degree.stdev * year.deflator
            self.earnings_power = max(100, np.random.normal(initial_salary, salary_std))
            self.years_experience = 0
        
        # Calculate growth based on experience
        # Apply annual growth rate with diminishing returns as experience increases
        # Ensure growth at least matches inflation to maintain real earnings
        experience_growth = self.degree.experience_growth 
        inflation_growth = year.inflation_rate  # Add inflation component
        growth_factor = 1 + experience_growth + inflation_growth
        
        # Apply growth to earnings power
        self.earnings_power *= growth_factor
        
        # Cap earnings at maximum multiple of initial salary (adjusted for inflation)
        max_earnings = self.degree.mean_earnings * 1.5 * year.deflator  # Using 1.5 as max multiplier
        self.earnings_power = min(self.earnings_power, max_earnings)
        
        # Track peak earnings
        if self.earnings_power > self.peak_earnings:
            self.peak_earnings = self.earnings_power
            self.peak_earnings_age = self.current_age
        
        # Increment years of experience
        self.years_experience += 1
        
        return self.earnings_power

    def calculate_counterfactual_earnings(self, relative_year: int, year: Year) -> float:
        """Calculate what the student would have earned without the program.
        
        Uses a household model where:
        - Household has multiple earners (default 2)
        - Control earner can earn more than other earner(s) via multiplier
        - Total household income is divided among all household members for consumption
        - No unemployment modeled in counterfactual (always employed)
        """
        # If past life expectancy, no earnings
        if self.starting_age + relative_year >= self.life_expectancy:
            return 0
        
        # Calculate total household income with multiple earners
        # Control earner can earn more than other earner(s) via multiplier
        params = self.counterfactual_params
        base_earnings = params.base_earnings
        
        # Total household income: control earner + other earners
        # Control earner: base_earnings * control_earner_multiplier
        # Other earners: base_earnings * (num_earners - 1)
        control_income = base_earnings * params.control_earner_multiplier
        other_earners_income = base_earnings * (params.num_earners - 1)
        total_household_income = control_income + other_earners_income
        
        # Per-person consumption (divide total income by household size)
        per_person_consumption = total_household_income / params.household_size_counterfactual
        
        return per_person_consumption * year.deflator

    def calculate_utility(self, income: float, alpha: float) -> float:
        """Calculate utility for a given income level."""
        return calculate_utility(income)

    def calculate_statistics(self, year: Year, eur_to_usd: float = 0.8458, ppp_multiplier: float = 0.4) -> Dict:
        """Calculate various statistics for the student's outcomes.
        
        Note on currency handling:
        - self.earnings: EUR (German salaries) - converted to USD for comparison/utility
        - self.counterfactual_earnings: USD (home country)
        - Remittances are calculated on EUR earnings, then converted to USD for utility calculations
        - eur_to_usd: Exchange rate to convert EUR to USD (default from GiveWell analysis)
        - ppp_multiplier: PPP adjustment for USD to home country purchasing power
        """
        # Convert EUR earnings to USD for comparison with counterfactual
        earnings_usd = self.earnings * eur_to_usd
        
        # Calculate total earnings and counterfactual earnings in real USD terms
        total_earnings_usd = np.sum(earnings_usd / year.deflator)
        total_earnings_eur = np.sum(self.earnings / year.deflator)  # Keep EUR for reference
        total_counterfactual = np.sum(self.counterfactual_earnings / year.deflator)  # Already USD
        earnings_gain = total_earnings_usd - total_counterfactual
        
        # Calculate remittances in USD
        # Remittances are sent from EUR earnings, converted to USD for receiving household
        remittance_rate = 0.08
        remittances_eur = self.earnings * remittance_rate / year.deflator
        remittances_usd = remittances_eur * eur_to_usd  # Convert to USD
        counterfactual_remittances = self.counterfactual_earnings * remittance_rate / year.deflator  # Already USD
        remittance_gain = np.sum(remittances_usd) - np.sum(counterfactual_remittances)
        
        # Calculate student utility using GiveWell's approach with moral weight of 1.44
        # All amounts in USD for consistent comparison
        moral_weight = 1.44  # GiveWell's moral weight (alpha)
        student_utility = np.sum([
            moral_weight * calculate_utility(e - r)  # Both in USD now
            for e, r in zip(earnings_usd / year.deflator, remittances_usd)
        ])
        counterfactual_utility = np.sum([
            moral_weight * calculate_utility(e - r)
            for e, r in zip(self.counterfactual_earnings / year.deflator, counterfactual_remittances)
        ])
        utility_gain = student_utility - counterfactual_utility
        
        # Calculate remittance utility using household model
        # Receiving household: 4 members (treated in Germany), 2 earners
        # Remittances are in USD, base_earnings is in USD - now consistent
        params = self.counterfactual_params
        remittance_utility = np.sum([
            calculate_remittance_utility(
                r,  # Already in USD
                base_earner_income=params.base_earnings,  # USD
                num_earners=params.num_earners,
                household_size_remittance=params.household_size_remittance,
                moral_weight=moral_weight
            )
            for r in remittances_usd
        ])
        counterfactual_remittance_utility = np.sum([
            calculate_remittance_utility(
                r,  # Already in USD
                base_earner_income=params.base_earnings,  # USD
                num_earners=params.num_earners,
                household_size_remittance=params.household_size_remittance,
                moral_weight=moral_weight
            )
            for r in counterfactual_remittances
        ])
        remittance_utility_gain = remittance_utility - counterfactual_remittance_utility
        
        # Calculate PPP-adjusted earnings gain (USD earnings gain converted to home country purchasing power)
        ppp_adjusted_earnings_gain = earnings_gain * ppp_multiplier
        
        # Calculate health benefits using GiveWell's approach
        # Life expectancy improvement from 62 to 81 years (19 years)
        # Value of 40 units for this improvement, discounted at 4%
        health_utility = 4.29  # Fixed value based on GiveWell's approach
        
        # Calculate follow-the-leader migration effects
        migration_utility = 0
        if self.is_graduated and not self.is_home:
            # Each successful graduate influences 0.05 additional people to migrate
            # They get the same utility gain as this student
            migration_utility = (utility_gain + remittance_utility_gain) * 0.05
        
        return {
            'earnings_gain': earnings_gain,  # USD
            'ppp_adjusted_earnings_gain': ppp_adjusted_earnings_gain,  # USD PPP-adjusted
            'remittance_gain': remittance_gain,  # USD
            'utility_gains': {
                'student_utility_gain': utility_gain,
                'remittance_utility_gain': remittance_utility_gain,
                'total_utility_gain': utility_gain + remittance_utility_gain
            },
            'health_utility': health_utility,
            'migration_utility': migration_utility,
            'total_earnings': total_earnings_usd,  # USD
            'total_earnings_eur': total_earnings_eur,  # EUR for reference
            'total_counterfactual': total_counterfactual,  # USD
            'total_remittances': np.sum(remittances_usd),  # USD
            'total_remittances_eur': np.sum(remittances_eur),  # EUR for reference
            'total_counterfactual_remittances': np.sum(counterfactual_remittances)  # USD
        }

@dataclass
class Contract:
    """Represents an ISA contract with a student"""
    student_id: int
    purchase_price: float
    remaining_payments: int
    total_payments: float = 0
    current_value: float = None
    is_active: bool = True
    exit_reason: str = None  # 'payment_cap', 'years_cap', 'home_return', 'default', None
    
    def __post_init__(self):
        self.current_value = self.purchase_price
    
    def record_payment(self, amount: float) -> None:
        """Record a payment and update contract value."""
        self.total_payments += amount
        self.remaining_payments = max(0, self.remaining_payments - 1)
        
        # Update current value based on remaining payments
        if self.remaining_payments > 0 and self.is_active:
            self.current_value = self.purchase_price * (self.remaining_payments / 10)
        else:
            self.current_value = 0
    
    def mark_exit(self, reason: str) -> None:
        """Mark contract as exited with the given reason."""
        self.is_active = False
        self.exit_reason = reason
        self.current_value = 0  # No value for inactive contracts

class InvestmentPool:
    """Manages the investment pool and tracks returns"""
    def __init__(self, initial_amount: float, isa_cap: float = 49500):
        self.initial_amount = initial_amount
        self.available_funds = initial_amount
        self.yearly_returns = 0
        self.yearly_cash = [initial_amount]
        self.contracts = []
        self.students = []  # Track all students
        self.isa_cap = isa_cap
        self.contract_metrics = {
            'total_contracts': 0,
            'payment_cap_exits': 0,
            'years_cap_exits': 0,
            'home_return_exits': 0,
            'default_exits': 0
        }
    
    def invest(self, amount: float, start_year: int, num_years: int) -> bool:
        """Invest in a new contract if funds are available."""
        if self.available_funds >= amount:
            self.available_funds -= amount
            contract = Contract(len(self.contracts), start_year, num_years)
            self.contracts.append(contract)
            self.contract_metrics['total_contracts'] += 1
            return True
        return False
    
    def add_student(self, student) -> None:
        """Add a student to the pool."""
        self.students.append(student)
    
    def receive_payment(self, amount: float, student_id: int) -> None:
        """Record a payment received from a student."""
        self.available_funds += amount
        self.yearly_returns += amount

    def mark_contract_exit(self, student_id: int, reason: str) -> None:
        """Mark a contract as exited for the given reason."""
        for contract in self.contracts:
            if contract.student_id == student_id and contract.is_active:
                contract.mark_exit(reason)
                self.contract_metrics[f'{reason}_exits'] += 1
                break
    
    def end_year(self) -> float:
        """Process end-of-year accounting and return cash flow for the year."""
        # Record cash for the year
        self.yearly_cash.append(self.available_funds)
        
        # Record cash flow for the year
        returns = self.yearly_returns
        self.yearly_returns = 0
        
        return returns
    
    def mark_remaining_as_defaulted(self) -> None:
        """Mark any remaining active contracts based on their status."""
        for contract in self.contracts:
            if contract.is_active:
                student = next((s for s in self.students if s.id == contract.student_id), None)
                if student:
                    # If they've made significant payments (>50% of cap), mark as years_cap
                    if np.sum(student.payments) >= self.isa_cap * 0.5:
                        self.mark_contract_exit(contract.student_id, 'years_cap')
                    # If they failed German acquisition (Kenya/Rwanda) or returned home
                    elif student.is_home:
                        self.mark_contract_exit(contract.student_id, 'home_return')
                    # If they're graduated and will return home
                    elif student.is_graduated and student.will_return_home:
                        self.mark_contract_exit(contract.student_id, 'home_return')
                    # Otherwise mark as default
                    else:
                        self.mark_contract_exit(contract.student_id, 'default')
                else:
                    self.mark_contract_exit(contract.student_id, 'default')
    
    def calculate_irr(self) -> float:
        """Calculate IRR using simplified ln(end/start)/years method."""
        if len(self.yearly_cash) < 2:
            return 0
        
        end_value = self.yearly_cash[-1]
        start_value = self.initial_amount
        years = len(self.yearly_cash) - 1
        
        if end_value <= 0 or start_value <= 0:
            return float('-inf')
        
        return np.log(end_value / start_value) / years

def calculate_remittance_utility(remittance_amount: float, base_consumption: float = None, 
                                  num_recipients: int = None, base_earner_income: float = 1503,
                                  num_earners: int = 2, household_size_remittance: int = 4,
                                  moral_weight: float = 1.44) -> float:
    """
    Calculate utility gain from remittances for family members.
    Uses GiveWell's approach of comparing log utilities of consumption with and without remittances.
    
    The receiving household model:
    - Household has num_earners earners (default 2), each earning base_earner_income
    - Treated person is in Germany, so household size is household_size_remittance (default 4)
    - Total household income is divided among all household members for base consumption
    - Remittances are added to this base consumption
    
    Args:
        remittance_amount: Annual remittance amount
        base_consumption: Base annual consumption per family member (if None, calculated from household model)
        num_recipients: Number of family members receiving remittances (if None, uses household_size_remittance)
        base_earner_income: Annual income per earner in the receiving household (default $1,503)
        num_earners: Number of earners in the receiving household (default 2)
        household_size_remittance: Size of receiving household (default 4, since treated is in Germany)
        moral_weight: Moral weight (alpha) for remittance utility, default 1.44 based on GiveWell
        
    Returns:
        Total utility gain from remittances across all recipients (with moral weight applied)
    """
    if remittance_amount <= 0:
        return 0
    
    # Use household model defaults if not specified
    if num_recipients is None:
        num_recipients = household_size_remittance
    
    # Calculate base consumption from household earnings if not specified
    if base_consumption is None:
        total_household_income = base_earner_income * num_earners
        base_consumption = total_household_income / household_size_remittance
        
    # Each recipient gets an equal share of remittances
    remittance_per_person = remittance_amount / num_recipients
    
    # Calculate utility gain per person: ln(base + remittance) - ln(base)
    # First year value per person is about 5.1 utils according to GiveWell
    utility_gain_per_person = np.log(base_consumption + remittance_per_person) - np.log(base_consumption)
    
    # Apply household multiplier of 1.2 from GiveWell BOTEC
    household_multiplier = 1.2
    
    # Total utility gain across all recipients with household multiplier and moral weight
    # According to GiveWell, this should be about 6.4 utils in the first year (before moral weight)
    # And about 63-101 utils when properly discounted over lifetime
    return moral_weight * utility_gain_per_person * num_recipients * household_multiplier

def calculate_student_utility(earnings: float, counterfactual: float, remittance: float, moral_weight: float = 1.44) -> float:
    """
    Calculate student's utility accounting for earnings gain and remittance costs.
    Uses GiveWell's approach of log utility with moral weight (alpha) parameter.
    
    Args:
        earnings: Total earnings
        counterfactual: Counterfactual earnings
        remittance: Amount sent as remittances
        moral_weight: Moral weight (alpha) for direct income effects, default 1.44 based on GiveWell
        
    Returns:
        Student's utility
    """
    if earnings <= counterfactual:
        return 0
    
    # Net disposable income after remittances
    net_gain = earnings - counterfactual - remittance
    
    if net_gain <= 0:
        return 0
        
    # Apply moral weight (alpha) to log utility
    return moral_weight * np.log(net_gain)

def calculate_total_utility(earnings: float, counterfactual: float, remittance_rate: float, moral_weight: float = 1.44,
                           base_earner_income: float = 1503, num_earners: int = 2, 
                           household_size_remittance: int = 4) -> Dict[str, float]:
    """
    Calculate total utility including both student and remittance impacts.
    
    Args:
        earnings: Total earnings
        counterfactual: Counterfactual earnings
        remittance_rate: Percentage of earnings sent as remittances
        moral_weight: Moral weight (alpha) for direct income effects
        base_earner_income: Annual income per earner in receiving household (default $1,503)
        num_earners: Number of earners in receiving household (default 2)
        household_size_remittance: Size of receiving household (default 4)
        
    Returns:
        Dictionary containing student utility, remittance utility, and total utility
    """
    remittance = earnings * remittance_rate
    
    student_utility = calculate_student_utility(earnings, counterfactual, remittance, moral_weight)
    remittance_utility = calculate_remittance_utility(
        remittance,
        base_earner_income=base_earner_income,
        num_earners=num_earners,
        household_size_remittance=household_size_remittance,
        moral_weight=moral_weight
    )
    
    return {
        'student_utility': student_utility,
        'remittance_utility': remittance_utility,
        'total_utility': student_utility + remittance_utility
    }

def calculate_student_statistics(student: Student, num_years: int, remittance_rate: float, impact_params: ImpactParams) -> Dict:
    """
    Calculate detailed statistics for a student.
    
    Parameters:
    - student: Student object
    - num_years: Number of years in simulation (this refers to the student's specific simulation duration)
    - remittance_rate: Percentage of income sent as remittances
    - impact_params: Parameters for impact calculation
    
    Returns:
    - Dictionary of student statistics
    
    Note on currency handling:
    - student.earnings: EUR (German salaries) - converted to USD for comparison/utility
    - student.counterfactual_earnings: USD (home country)
    - Remittances are calculated on EUR earnings, then converted to USD for utility calculations
    - The eur_to_usd rate converts EUR to USD: EUR_amount * eur_to_usd = USD_amount
    """
    # FX conversion rate (EUR to USD)
    eur_to_usd = impact_params.eur_to_usd
    
    # Convert EUR earnings to USD for comparison with counterfactual
    # student.earnings are in EUR (German salaries)
    # student.counterfactual_earnings are in USD (home country earnings)
    earnings_usd = student.earnings * eur_to_usd
    
    # Calculate lifetime earnings in USD (undiscounted sum)
    lifetime_earnings_usd = np.sum(earnings_usd)
    
    # Keep EUR earnings for reference (ISA calculations use EUR)
    lifetime_earnings_eur = np.sum(student.earnings)
    
    # Calculate real (present value) earnings in USD, discounted to absolute simulation year 0
    if len(earnings_usd) == 0:
        lifetime_real_earnings_usd = 0.0
    else:
        # 't' is the index relative to the start of the student's earnings array.
        # Earning at student.earnings[t] occurred in absolute simulation year 'student.start_year + t'.
        discount_factors_for_pv_earnings = np.array([(1 / (1 + impact_params.discount_rate)) ** (student.start_year + t) for t in range(len(earnings_usd))])
        lifetime_real_earnings_usd = np.sum(earnings_usd * discount_factors_for_pv_earnings)
    
    # Calculate counterfactual lifetime earnings (undiscounted sum) - already in USD
    counterfactual_lifetime_earnings = np.sum(student.counterfactual_earnings) 

    # Calculate remittances in USD
    # Remittances are sent from EUR earnings, converted to USD for receiving household
    # remittance_rate is applied to EUR earnings, then converted to USD
    lifetime_remittances_eur = lifetime_earnings_eur * remittance_rate
    lifetime_remittances_usd = lifetime_remittances_eur * eur_to_usd
    counterfactual_remittances = counterfactual_lifetime_earnings * impact_params.counterfactual.remittance_rate
    
    # Calculate yearly utilities with proper discounting to absolute simulation year 0
    # All utility calculations use USD amounts for consistency
    yearly_utilities = []
    yearly_counterfactual_utilities = []
    
    # Get household parameters from counterfactual params
    cf_params = impact_params.counterfactual
    
    for idx_relative_to_student_earnings in range(len(student.earnings)):
        absolute_simulation_year = student.start_year + idx_relative_to_student_earnings
        discount_factor = (1 / (1 + impact_params.discount_rate)) ** absolute_simulation_year
        
        # Convert this year's EUR earnings to USD
        year_earnings_usd = student.earnings[idx_relative_to_student_earnings] * eur_to_usd
        
        # Calculate per-year undiscounted utilities (all in USD)
        year_utils = calculate_total_utility(
            year_earnings_usd,  # USD
            student.counterfactual_earnings[idx_relative_to_student_earnings],  # USD
            remittance_rate,  # Rate applied to USD earnings
            impact_params.moral_weight,
            base_earner_income=cf_params.base_earnings,  # USD
            num_earners=cf_params.num_earners,
            household_size_remittance=cf_params.household_size_remittance
        )
        # Discount and store
        for key in year_utils:
            year_utils[key] *= discount_factor
        yearly_utilities.append(year_utils)
        
        # Calculate per-year undiscounted counterfactual utilities (already in USD)
        counterfactual_utils = calculate_total_utility(
            student.counterfactual_earnings[idx_relative_to_student_earnings],  # USD
            0,  # No counterfactual to counterfactual
            cf_params.remittance_rate,
            impact_params.moral_weight,
            base_earner_income=cf_params.base_earnings,  # USD
            num_earners=cf_params.num_earners,
            household_size_remittance=cf_params.household_size_remittance
        )
        # Discount and store
        for key in counterfactual_utils:
            counterfactual_utils[key] *= discount_factor
        yearly_counterfactual_utilities.append(counterfactual_utils)
    
    # Sum discounted yearly utilities to get total present values
    total_student_utility = sum(u['student_utility'] for u in yearly_utilities)
    total_remittance_utility = sum(u['remittance_utility'] for u in yearly_utilities)
    total_utility = sum(u['total_utility'] for u in yearly_utilities)
    
    counterfactual_student_utility = sum(u['student_utility'] for u in yearly_counterfactual_utilities)
    counterfactual_remittance_utility = sum(u['remittance_utility'] for u in yearly_counterfactual_utilities)
    counterfactual_total_utility = sum(u['total_utility'] for u in yearly_counterfactual_utilities)
    
    utility_gains = {
        'student_utility_gain': total_student_utility - counterfactual_student_utility,
        'remittance_utility_gain': total_remittance_utility - counterfactual_remittance_utility,
        'total_utility_gain': total_utility - counterfactual_total_utility
    }
    
    years_employed = np.sum(student.employment_history)
    total_isa_payments = np.sum(student.payments) # Undiscounted sum, in EUR
    
    # Earnings gain in USD (both amounts now in USD)
    earnings_gain_usd = lifetime_earnings_usd - counterfactual_lifetime_earnings
    
    # Remittance gain in USD
    remittance_gain_usd = lifetime_remittances_usd - counterfactual_remittances
    
    # PPP-adjusted earnings gain (based on undiscounted USD earnings gain)
    # PPP multiplier converts USD to home country purchasing power
    ppp_adjusted_earnings_gain = earnings_gain_usd * impact_params.ppp_multiplier
    
    # Health utility: Fixed value of 3.0 utils, discounted to PV from graduation time.
    health_utility_pv = 0.0
    if student.is_graduated:
        # student.actual_years_to_complete is relative to the student's start.
        # For Kenya/Rwanda, add german_learning_years to account for time before studies began
        year_of_health_benefit_realization = student.start_year + student.german_learning_years + student.actual_years_to_complete
        health_utility_pv = 4.29 * ((1 / (1 + impact_params.discount_rate)) ** year_of_health_benefit_realization)

    # Migration utility (based on already discounted total_utility_gain)
    migration_utility_pv = 0.0
    if student.is_graduated and not student.is_home:
        migration_utility_pv = utility_gains['total_utility_gain'] * impact_params.migration_influence_factor # total_utility_gain is already PV
    
    utility_gains['health_utility_gain'] = health_utility_pv 
    utility_gains['migration_influence_utility_gain'] = migration_utility_pv 
    utility_gains['total_utility_gain_with_extras'] = (
        utility_gains['total_utility_gain'] + 
        health_utility_pv + 
        migration_utility_pv
    )
    
    return {
        'degree_type': student.degree.name,
        'graduated': student.is_graduated,
        'dropped_out': not student.is_graduated,
        'lifetime_earnings': lifetime_earnings_usd,  # USD, undiscounted
        'lifetime_earnings_eur': lifetime_earnings_eur,  # EUR, undiscounted (for reference)
        'lifetime_real_earnings': lifetime_real_earnings_usd,  # USD, discounted to year 0
        'counterfactual_lifetime_earnings': counterfactual_lifetime_earnings,  # USD, undiscounted
        'earnings_gain': earnings_gain_usd,  # USD, undiscounted
        'ppp_adjusted_earnings_gain': ppp_adjusted_earnings_gain,  # USD PPP-adjusted
        'lifetime_remittances': lifetime_remittances_usd,  # USD, undiscounted
        'lifetime_remittances_eur': lifetime_remittances_eur,  # EUR, undiscounted (for reference)
        'counterfactual_remittances': counterfactual_remittances,  # USD, undiscounted
        'remittance_gain': remittance_gain_usd,  # USD, undiscounted
        'utility_gains': utility_gains,  # All components are PVs
        'health_utility': health_utility_pv,  # PV of fixed health utility
        'migration_utility': migration_utility_pv,  # PV of migration utility
        'years_employed': years_employed,
        'total_isa_payments': total_isa_payments,  # EUR, undiscounted sum
        'years_paid_isa': student.years_paid,
        'hit_payment_cap': student.hit_cap,
        'yearly_utilities': yearly_utilities,  # List of dicts, values already discounted to year 0
        'yearly_counterfactual_utilities': yearly_counterfactual_utilities  # List of dicts, values already discounted to year 0
    }

def simulate_impact(
    program_type: str,
    initial_investment: float,
    num_years: int,
    impact_params: ImpactParams,
    num_sims: int = 1,
    scenario: str = 'baseline',
    remittance_rate: float = 0.08,
    home_prob: float = 0,
    data_callback: Optional[Callable] = None,
    isa_percentage: Optional[float] = None,
    isa_cap: Optional[float] = None,
    isa_threshold: Optional[float] = None,
    price_per_student: Optional[float] = None,
    initial_inflation_rate: float = 0.02,
    initial_unemployment_rate: float = 0.1,
    degree_params: Optional[List[tuple]] = None,
    stipend_income: Optional[float] = None,
    stipend_std: Optional[float] = None
) -> Dict:
    """
    Run a simulation of the impact of an ISA program.
    
    Parameters:
    - program_type: Type of program ('University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda))
    - initial_investment: Initial investment amount
    - num_years: Number of years to simulate
    - impact_params: Parameters for measuring social impact
    - num_sims: Number of simulations to run
    - scenario: Predefined scenario to use
    - remittance_rate: Percentage of income sent as remittances
    - home_prob: Probability of returning home after graduation
    - data_callback: Function to call with yearly data
    - isa_percentage: Percentage of income to pay in ISA
    - isa_cap: Maximum amount to pay in ISA
    - isa_threshold: Minimum income threshold for ISA payments
    - price_per_student: Cost per student
    - initial_inflation_rate: Initial inflation rate
    - initial_unemployment_rate: Initial unemployment rate
    - degree_params: Custom degree parameters
    - stipend_income: Pre-graduation stipend income (e.g. side job + stipend in Germany)
    - stipend_std: Standard deviation of stipend income
    
    Returns:
    - Dictionary of simulation results
    """
    # Set default ISA parameters based on program type if not provided
    if isa_percentage is None:
        if program_type == 'University':  # Uganda program
            isa_percentage = 0.14
        elif program_type == 'Nurse':     # Kenya program
            isa_percentage = 0.12
        elif program_type == 'Trade':     # Rwanda program
            isa_percentage = 0.12
        else:
            isa_percentage = 0.12
    
    if isa_cap is None:
        if program_type == 'University':  # Uganda program
            isa_cap = 72500
        elif program_type == 'Nurse':     # Kenya program
            isa_cap = 49950
        elif program_type == 'Trade':     # Rwanda program
            isa_cap = 45000
        else:
            isa_cap = 50000
    
    if isa_threshold is None:
        isa_threshold = 27000
    
    if price_per_student is None:
        if program_type == 'University':  # Uganda program
            price_per_student = 30012  # GiveWell analysis cost per student
        elif program_type == 'Nurse':     # Kenya program
            price_per_student = 16650
        elif program_type == 'Trade':     # Rwanda program
            price_per_student = 16650
        else:
            raise ValueError("Program type must be 'University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda)")
    
    # Set default stipend for University (Uganda) program - represents side job + first year stipend
    # Uganda students are already in Germany, so no German learning phase
    # GiveWell: $1032/month nominal = $1320/month real (PPP-adjusted) = $15,840/year real
    if program_type == 'University':
        if stipend_income is None:
            stipend_income = 15840  # GiveWell: $1320/month real (PPP-adjusted) × 12 months
        if stipend_std is None:
            stipend_std = 1500  # Proportionally scaled std dev
        german_learning_years = 0
        study_income = 0
    else:
        # Kenya/Rwanda programs have 1 year German learning phase
        # Students earn counterfactual income during German learning, then €14k during studies
        if stipend_income is None:
            stipend_income = 0
        if stipend_std is None:
            stipend_std = 0
        german_learning_years = 1
        study_income = 14000  # €14k/year during studies in Germany
    
    # Initialize economic conditions
    year = Year(
        initial_inflation_rate=initial_inflation_rate,
        initial_unemployment_rate=initial_unemployment_rate,
        initial_isa_cap=isa_cap,
        initial_isa_threshold=isa_threshold,
        num_years=num_years
    )
    
    # Initialize investment pool
    pool = InvestmentPool(initial_amount=initial_investment, isa_cap=isa_cap)
    
    # Get degree parameters for the scenario
    if degree_params is None:
        degree_params = get_degree_for_scenario(scenario, program_type, home_prob)
    
    # Convert DegreeParams to Degree objects
    degrees_with_weights = [
        (Degree(
            name=dp.name,
            mean_earnings=dp.initial_salary,
            stdev=dp.salary_std,
            experience_growth=dp.annual_growth,
            years_to_complete=dp.years_to_complete,
            home_prob=dp.home_prob
        ), weight)
        for dp, weight in degree_params
    ]
    
    # Initialize students
    students = []
    for i in range(60):  # Start with 60 students
        degree_type = np.random.choice([d[0] for d in degrees_with_weights], p=[d[1] for d in degrees_with_weights])
        student = Student(degree_type, num_years, impact_params.counterfactual,
                         stipend_income=stipend_income, stipend_std=stipend_std,
                         german_learning_years=german_learning_years, study_income=study_income)
        student.id = i
        students.append(student)
        pool.add_student(student)  # Add student to pool
        # Use initial price (no inflation adjustment needed for year 0)
        pool.invest(price_per_student, 0, num_years)
    
    # Track yearly data
    yearly_data = []
    
    # Track earnings by degree type each year
    earnings_by_degree_yearly = []
    
    # Run simulation
    for i in range(num_years):
        # Process each student
        for student in students:
            if i < student.start_year:
                continue
            
            # Calculate earnings
            relative_year = i - student.start_year
            
            # Normal earnings calculation
            earnings = student.calculate_earnings(relative_year, year)
            student.earnings[relative_year] = earnings
            
            # Calculate counterfactual earnings
            counterfactual = student.calculate_counterfactual_earnings(relative_year, year)
            student.counterfactual_earnings[relative_year] = counterfactual
            
            # Check for German failure (Kenya/Rwanda students who didn't acquire German)
            if student.german_learning_years > 0 and student.passed_german == False and relative_year == student.german_learning_years:
                # They failed German at the end of learning phase, mark as home return
                pool.mark_contract_exit(student.id, 'home_return')
                continue
            
            # Check for home return after graduation
            if student.is_graduated and student.will_return_home and relative_year >= student.german_learning_years + student.actual_years_to_complete:
                # Mark contract as exited
                pool.mark_contract_exit(student.id, 'home_return')
                # Note: earnings are already handled in calculate_earnings method
                continue
            
            # Process ISA payments if applicable
            if student.is_graduated and not student.hit_cap:
                if student.current_unemployment_spell > 2:  # Default after 2 years unemployment
                    pool.mark_contract_exit(student.id, 'default')
                    continue
                
                # Check if earnings exceed threshold
                if earnings > year.isa_threshold:
                    student.years_paid += 1
                    
                    # Check if years cap is reached
                    if student.years_paid >= 10:  # 10-year payment cap
                        pool.mark_contract_exit(student.id, 'years_cap')
                        continue
                    
                    # Calculate payment
                    payment = min(
                        earnings * isa_percentage,
                        year.isa_cap - np.sum(student.payments)
                    )
                    
                    # Check if payment cap is reached
                    if np.sum(student.payments) + payment >= year.isa_cap:
                        payment = year.isa_cap - np.sum(student.payments)
                        student.hit_cap = True
                        pool.mark_contract_exit(student.id, 'payment_cap')
                    
                    # Record payment in student and contract
                    student.payments[relative_year] = payment
                    student.real_payments[relative_year] = payment / year.deflator
                    
                    # Find and update the student's contract
                    for contract in pool.contracts:
                        if contract.student_id == student.id and contract.is_active:
                            contract.record_payment(payment)
                            break
                    
                    # Update pool
                    pool.receive_payment(payment / year.deflator, student.id)
        
        # Collect earnings by degree type for this year
        # Note: student.earnings are in EUR, student.counterfactual_earnings are in USD
        # We track both EUR and USD values for transparency
        eur_to_usd = impact_params.eur_to_usd
        degree_earnings = {}
        for student in students:
            if i < student.start_year:
                continue
            relative_year = i - student.start_year
            degree_name = student.degree.name
            
            if degree_name not in degree_earnings:
                degree_earnings[degree_name] = {
                    'count': 0,
                    'total_earnings_eur': 0.0,  # EUR earnings
                    'total_earnings_usd': 0.0,  # EUR earnings converted to USD
                    'total_counterfactual': 0.0,  # USD (home country)
                    'total_remittances_eur': 0.0,  # EUR remittances
                    'total_remittances_usd': 0.0,  # EUR remittances converted to USD
                    'graduated_count': 0,
                    'in_germany_count': 0,
                    'at_home_count': 0
                }
            
            earnings_eur = student.earnings[relative_year]
            earnings_usd = earnings_eur * eur_to_usd
            counterfactual_usd = student.counterfactual_earnings[relative_year]
            remittances_eur = earnings_eur * remittance_rate
            remittances_usd = remittances_eur * eur_to_usd
            
            degree_earnings[degree_name]['count'] += 1
            degree_earnings[degree_name]['total_earnings_eur'] += earnings_eur
            degree_earnings[degree_name]['total_earnings_usd'] += earnings_usd
            degree_earnings[degree_name]['total_counterfactual'] += counterfactual_usd
            degree_earnings[degree_name]['total_remittances_eur'] += remittances_eur
            degree_earnings[degree_name]['total_remittances_usd'] += remittances_usd
            
            if student.is_graduated:
                degree_earnings[degree_name]['graduated_count'] += 1
            if hasattr(student, 'in_germany') and student.in_germany:
                degree_earnings[degree_name]['in_germany_count'] += 1
            if student.is_home:
                degree_earnings[degree_name]['at_home_count'] += 1
        
        # Calculate averages
        for degree_name in degree_earnings:
            count = degree_earnings[degree_name]['count']
            if count > 0:
                degree_earnings[degree_name]['avg_earnings'] = degree_earnings[degree_name]['total_earnings_usd'] / count  # USD for comparison
                degree_earnings[degree_name]['avg_earnings_eur'] = degree_earnings[degree_name]['total_earnings_eur'] / count
                degree_earnings[degree_name]['avg_counterfactual'] = degree_earnings[degree_name]['total_counterfactual'] / count
                degree_earnings[degree_name]['avg_remittances'] = degree_earnings[degree_name]['total_remittances_usd'] / count  # USD for comparison
                degree_earnings[degree_name]['avg_remittances_eur'] = degree_earnings[degree_name]['total_remittances_eur'] / count
            else:
                degree_earnings[degree_name]['avg_earnings'] = 0
                degree_earnings[degree_name]['avg_earnings_eur'] = 0
                degree_earnings[degree_name]['avg_counterfactual'] = 0
                degree_earnings[degree_name]['avg_remittances'] = 0
                degree_earnings[degree_name]['avg_remittances_eur'] = 0
        
        earnings_by_degree_yearly.append({
            'year': i,
            'by_degree': degree_earnings
        })
        
        # End year and capture data
        returns = pool.end_year()
        
        # Reinvest available funds in new students if possible
        if i < num_years - 15 and pool.available_funds > price_per_student:
            cash_reserve = initial_investment * 0.02  # Reduce cash reserve to 2%
            available_for_investment = max(0, pool.available_funds - cash_reserve)
            
            # Adjust price per student for inflation
            current_price = price_per_student * year.deflator
            max_new_students = int(available_for_investment / current_price)
            
            # Fund as many students as possible with available funds
            num_new_students = max_new_students
            
            for _ in range(num_new_students):
                degree_type = np.random.choice([d[0] for d in degrees_with_weights], p=[d[1] for d in degrees_with_weights])
                student = Student(degree_type, num_years - i, impact_params.counterfactual,
                                 stipend_income=stipend_income, stipend_std=stipend_std,
                                 german_learning_years=german_learning_years, study_income=study_income)
                student.id = len(students)
                student.start_year = i
                students.append(student)
                pool.add_student(student)  # Add student to pool
                
                if not pool.invest(current_price, i, num_years):
                    break
        
        # Call data callback if provided
        if data_callback:
            yearly_data.append({
                'year': i,
                'cash': pool.available_funds,
                'total_contracts': pool.contract_metrics['total_contracts'],
                'active_contracts': len([c for c in pool.contracts if c.is_active]),
                'returns': returns,
                'exits': {k: v for k, v in pool.contract_metrics.items() if k != 'total_contracts'}
            })
            
            # Actually call the callback function
            data_callback(
                i,
                pool.available_funds,
                pool.contract_metrics['total_contracts'],
                len([c for c in pool.contracts if c.is_active]),
                returns,
                sum(pool.contract_metrics[k] for k in ['payment_cap_exits', 'years_cap_exits', 'home_return_exits', 'default_exits'])
            )
    
    # Mark any remaining active contracts as defaulted
    pool.mark_remaining_as_defaulted()
    
    # Calculate final metrics
    final_irr = pool.calculate_irr()
    total_students_educated = len([s for s in students if s.is_graduated])
    
    # Calculate student impact metrics
    student_metrics = {
        'avg_student_utility_gain': 0.0,
        'avg_remittance_utility_gain': 0.0,
        'avg_health_utility_gain': 0.0,
        'avg_migration_utility_gain': 0.0,
        'avg_total_utility_gain': 0.0,
        'avg_total_utility_gain_with_extras': 0.0,
        'avg_earnings_gain': 0.0,
        'avg_ppp_adjusted_earnings_gain': 0.0,
        'avg_remittance_gain': 0.0
    }
    
    if students:
        total_student_utility = 0.0
        total_remittance_utility = 0.0
        total_health_utility = 0.0
        total_migration_utility = 0.0
        total_earnings_gain = 0.0
        total_ppp_adjusted_earnings_gain = 0.0
        total_remittance_gain = 0.0
        num_graduated = 0
        
        for student in students:
            if student.is_graduated:
                stats = student.calculate_statistics(year, eur_to_usd=impact_params.eur_to_usd, ppp_multiplier=impact_params.ppp_multiplier)
                total_student_utility += stats['utility_gains']['student_utility_gain']
                total_remittance_utility += stats['utility_gains']['remittance_utility_gain']
                total_health_utility += stats['health_utility']
                total_migration_utility += stats['migration_utility']
                total_earnings_gain += stats['earnings_gain']
                total_ppp_adjusted_earnings_gain += stats['ppp_adjusted_earnings_gain']
                total_remittance_gain += stats['remittance_gain']
                num_graduated += 1
        
        if num_graduated > 0:
            student_metrics = {
                'avg_student_utility_gain': total_student_utility / num_graduated,
                'avg_remittance_utility_gain': total_remittance_utility / num_graduated,
                'avg_health_utility_gain': total_health_utility / num_graduated,
                'avg_migration_utility_gain': total_migration_utility / num_graduated,
                'avg_total_utility_gain': (total_student_utility + total_remittance_utility) / num_graduated,
                'avg_total_utility_gain_with_extras': (total_student_utility + total_remittance_utility + 
                                                     total_health_utility + total_migration_utility) / num_graduated,
                'avg_earnings_gain': total_earnings_gain / num_graduated,
                'avg_ppp_adjusted_earnings_gain': total_ppp_adjusted_earnings_gain / num_graduated,
                'avg_remittance_gain': total_remittance_gain / num_graduated
            }
            
            # Calculate percentage breakdown of utility sources
            total_utility = (total_student_utility + total_remittance_utility + 
                           total_health_utility + total_migration_utility)
            if total_utility > 0:
                student_metrics['direct_income_pct'] = (total_student_utility / total_utility) * 100
                student_metrics['remittance_pct'] = (total_remittance_utility / total_utility) * 100
                student_metrics['health_pct'] = (total_health_utility / total_utility) * 100
                student_metrics['migration_influence_pct'] = (total_migration_utility / total_utility) * 100
    
    # Verify contract accounting
    total_exits = sum(pool.contract_metrics[k] for k in ['payment_cap_exits', 'years_cap_exits', 'home_return_exits', 'default_exits'])
    assert total_exits == pool.contract_metrics['total_contracts'], "Contract tracking mismatch"
    
    # Calculate total payments
    total_payments = sum(contract.total_payments for contract in pool.contracts)
    
    return {
        'initial_investment': initial_investment,
        'final_cash': pool.available_funds,
        'irr': final_irr,
        'total_students': len(students),
        'students_educated': total_students_educated,
        'contract_metrics': pool.contract_metrics,
        'yearly_data': yearly_data,
        'student_metrics': student_metrics,
        'total_payments': total_payments,
        'earnings_by_degree_yearly': earnings_by_degree_yearly
    }

def run_impact_simulation(
    program_type: str,
    initial_investment: float,
    num_years: int,
    impact_params: ImpactParams,
    num_sims: int = 1,
    scenario: str = 'baseline',
    remittance_rate: float = 0.15,
    home_prob: float = 0,
    data_callback: Optional[Callable] = None,
    isa_percentage: Optional[float] = None,
    isa_cap: Optional[float] = None,
    isa_threshold: Optional[float] = None,
    price_per_student: Optional[float] = None,
    initial_inflation_rate: float = 0.02,
    initial_unemployment_rate: float = 0.1,
    degree_params: Optional[List[tuple]] = None,
    stipend_income: Optional[float] = None,
    stipend_std: Optional[float] = None
) -> Dict:
    """
    Run multiple simulations of the ISA program and aggregate results.
    
    Args:
        program_type (str): Type of program ('University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda))
        initial_investment (float): Initial investment amount
        num_years (int): Number of years to simulate
        impact_params (ImpactParams): Parameters for impact calculation
        num_sims (int): Number of simulations to run
        scenario (str): Scenario type ('baseline', 'optimistic', 'pessimistic')
        remittance_rate (float): Percentage of income sent as remittances
        home_prob (float): Probability of returning home
        data_callback (callable): Function to call with yearly financial data
        isa_percentage (float, optional): ISA percentage of income
        isa_cap (float, optional): Maximum ISA payment cap
        isa_threshold (float, optional): Minimum income threshold for ISA payments
        price_per_student (float, optional): Cost per student
        initial_inflation_rate (float): Starting inflation rate
        initial_unemployment_rate (float): Starting unemployment rate
        degree_params (List[tuple], optional): List of (DegreeParams, weight) tuples
        stipend_income (float, optional): Pre-graduation stipend income (e.g. side job + stipend in Germany)
        stipend_std (float, optional): Standard deviation of stipend income
        
    Returns:
        dict: Aggregated simulation results
    """
    # Set defaults based on program type
    if isa_percentage is None:
        if program_type == 'University':  # Uganda program
            isa_percentage = 0.14
        elif program_type == 'Nurse':     # Kenya program
            isa_percentage = 0.12
        elif program_type == 'Trade':     # Rwanda program
            isa_percentage = 0.12
        else:
            isa_percentage = 0.12
    
    if isa_cap is None:
        if program_type == 'University':  # Uganda program
            isa_cap = 72500
        elif program_type == 'Nurse':     # Kenya program
            isa_cap = 49950
        elif program_type == 'Trade':     # Rwanda program
            isa_cap = 45000
        else:
            isa_cap = 50000
    
    if price_per_student is None:
        if program_type == 'University':  # Uganda program
            price_per_student = 30012  # GiveWell analysis cost per student
        elif program_type == 'Nurse':     # Kenya program
            price_per_student = 16650
        elif program_type == 'Trade':     # Rwanda program
            price_per_student = 16650
        else:
            raise ValueError("Program type must be 'University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda)")
        
    if isa_threshold is None:
        isa_threshold = 27000
    
    # Run simulations
    simulation_results = []
    for sim in range(num_sims):
        # Run single simulation
        result = simulate_impact(
            program_type=program_type,
            initial_investment=initial_investment,
            num_years=num_years,
            impact_params=impact_params,
            num_sims=1,
            scenario=scenario,
            remittance_rate=remittance_rate,
            home_prob=home_prob,
            data_callback=data_callback if sim == 0 else None,  # Only use callback for first simulation
            isa_percentage=isa_percentage,
            isa_cap=isa_cap,
            isa_threshold=isa_threshold,
            price_per_student=price_per_student,
            initial_inflation_rate=initial_inflation_rate,
            initial_unemployment_rate=initial_unemployment_rate,
            degree_params=degree_params,
            stipend_income=stipend_income,
            stipend_std=stipend_std
        )
        simulation_results.append(result)
    
    # Aggregate results
    aggregated = aggregate_simulation_results(simulation_results)
    
    return {
        'program_type': program_type,
        'initial_investment': initial_investment,
        'price_per_student': price_per_student,
        'isa_percentage': isa_percentage,
        'isa_threshold': isa_threshold,
        'isa_cap': isa_cap,
        'impact_metrics': aggregated['impact_metrics'],
        'financial_metrics': aggregated['financial_metrics'],
        'time_series': aggregated['time_series'],
        'student_outcomes': aggregated['student_outcomes'],
        'irr': simulation_results[0]['irr'] if num_sims == 1 else None,
        'simulation_results': simulation_results
    }

def get_degree_for_scenario(scenario: str, program_type: str, home_prob: float, degree_params=None) -> List[tuple]:
    """
    Helper function to get appropriate degrees and their weights based on scenario.
    
    Returns:
        List of tuples (DegreeParams, weight)
    """
    if degree_params:
        return degree_params
    
    if program_type == 'University':  # Uganda program
        # For University programs
        # All asst in Uganda program should be moved to asst_shift (students begin pursuing bachelors)
        return [
            (DegreeParams(
                name='BA',
                initial_salary=41300,
                salary_std=6000,
                annual_growth=0.03,
                years_to_complete=4,
                home_prob=home_prob
            ), 0.7),  # 70% BA
            (DegreeParams(
                name='MA',
                initial_salary=46709,
                salary_std=6600,
                annual_growth=0.04,
                years_to_complete=6,
                home_prob=home_prob
            ), 0.2),   # 20% MA
            (DegreeParams(
                name='ASST_SHIFT',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,  # Longer time to complete (6 years)
                home_prob=home_prob
            ), 0.1)    # 10% ASST_SHIFT (students who begin pursuing bachelors but shift to assistant)
        ]
    elif program_type == 'Nurse':  # Kenya program
        # For Nurse programs
        # 33% of ASST should be moved to asst_shift
        asst_percentage = 0.60
        asst_shift_percentage = asst_percentage * 0.33
        regular_asst_percentage = asst_percentage - asst_shift_percentage
        
        return [
            (DegreeParams(
                name='NURSE',
                initial_salary=40000,
                salary_std=4000,
                annual_growth=0.02,
                years_to_complete=4,
                home_prob=home_prob
            ), 0.25),  # 25% NURSE
            (DegreeParams(
                name='ASST',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=3,
                home_prob=home_prob
            ), regular_asst_percentage),  # ~40% ASST
            (DegreeParams(
                name='ASST_SHIFT',
                initial_salary=31500,  # Same salary as ASST
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,  # Longer time to complete (6 years)
                home_prob=home_prob
            ), asst_shift_percentage),  # ~20% ASST_SHIFT
            (DegreeParams(
                name='NA',
                initial_salary=1100,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0  # Fixed high home probability for NA
            ), 0.15)   # 15% NA
        ]
    elif program_type == 'Trade':  # Rwanda program
        # For Trade programs
        # 33% of ASST should be moved to asst_shift
        asst_percentage = 0.40
        asst_shift_percentage = asst_percentage * 0.33
        regular_asst_percentage = asst_percentage - asst_shift_percentage
        
        return [
            (DegreeParams(
                name='TRADE',
                initial_salary=35000,
                salary_std=3000,
                annual_growth=0.02,
                years_to_complete=3,
                home_prob=home_prob
            ), 0.40),  # 40% TRADE
            (DegreeParams(
                name='ASST',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=3,
                home_prob=home_prob
            ), regular_asst_percentage),  # ~27% ASST
            (DegreeParams(
                name='ASST_SHIFT',
                initial_salary=31500,  # Same salary as ASST
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,  # Longer time to complete (6 years)
                home_prob=home_prob
            ), asst_shift_percentage),  # ~13% ASST_SHIFT
            (DegreeParams(
                name='NA',
                initial_salary=1100,
                salary_std=100,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0  # Fixed high home probability for NA
            ), 0.20)   # 20% NA
        ]
    else:
        raise ValueError("Program type must be 'University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda)")

def aggregate_simulation_results(results: List[Dict]) -> Dict:
    """Aggregate results across multiple simulations"""
    num_sims = len(results)
    
    # Calculate averages for impact metrics
    impact_metrics = {
        'avg_utility_gain': np.mean([
            r['student_metrics']['avg_total_utility_gain']
            for r in results
        ]),
        'avg_earnings_gain': np.mean([
            r['student_metrics']['avg_earnings_gain']
            for r in results
        ]),
        'avg_remittance_gain': np.mean([
            r['student_metrics']['avg_remittance_gain']
            for r in results
        ])
    }
    
    # Calculate financial metrics
    financial_metrics = {
        'avg_total_payments': np.mean([r['total_payments'] for r in results]),
        'avg_students_funded': np.mean([r['total_students'] for r in results])
    }
    
    # Aggregate time series data if available
    time_series = {}
    if results[0].get('yearly_data'):
        yearly_data = [r['yearly_data'] for r in results]
        time_series = {
            'cash': np.mean([
                [year['cash'] for year in sim_data]
                for sim_data in yearly_data
            ], axis=0),
            'returns': np.mean([
                [year['returns'] for year in sim_data]
                for sim_data in yearly_data
            ], axis=0),
            'active_contracts': np.mean([
                [year['active_contracts'] for year in sim_data]
                for sim_data in yearly_data
            ], axis=0)
        }
    
    # Calculate student outcomes
    student_outcomes = {
        'graduation_rate': np.mean([
            r['students_educated'] / r['total_students']
            for r in results
        ]),
        'avg_irr': np.mean([r['irr'] for r in results])
    }
    
    return {
        'impact_metrics': impact_metrics,
        'financial_metrics': financial_metrics,
        'time_series': time_series,
        'student_outcomes': student_outcomes
    }

def _calculate_graduation_delay(base_years_to_complete: int, degree_name: str = '') -> int:
    """
    Calculate a realistic graduation delay based on degree-specific distributions.
    
    For BA and ASST degrees:
    - 50% graduate on time (no delay)
    - 25% graduate 1 year late (50% of remaining)
    - 12.5% graduate 2 years late (50% of remaining)
    - 6.25% graduate 3 years late (50% of remaining)
    - The rest (6.25%) graduate 4 years late
    
    For MA, NURSE, and TRADE degrees:
    - 75% graduate on time (no delay)
    - 20% graduate 1 year late
    - 2.5% graduate 2 years late
    - 2.5% graduate 3 years late
    
    Args:
        base_years_to_complete: The nominal years to complete the degree
        degree_name: The type of degree (BA, MA, ASST, NURSE, TRADE, etc.)
        
    Returns:
        Total years to complete including delay
    """
    rand = np.random.random()
    
    # Apply special distribution for Masters, Nurse, and Trade degrees
    if degree_name in ['MA', 'NURSE', 'TRADE']:
        if rand < 0.75:
            return base_years_to_complete  # Graduate on time
        elif rand < 0.95:
            return base_years_to_complete + 1  # 1 year late
        elif rand < 0.975:
            return base_years_to_complete + 2  # 2 years late
        else:
            return base_years_to_complete + 3  # 3 years late
    else:
        # Default distribution for other degrees (BA, ASST, NA, etc.)
        if rand < 0.5:
            return base_years_to_complete  # Graduate on time
        elif rand < 0.75:
            return base_years_to_complete + 1  # 1 year late
        elif rand < 0.875:
            return base_years_to_complete + 2  # 2 years late
        elif rand < 0.9375:
            return base_years_to_complete + 3  # 3 years late
        else:
            return base_years_to_complete + 4  # 4 years late

def main():
    """
    Main function to demonstrate the usage of the ISA impact model.
    
    This function runs several example simulations and prints the results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ISA impact simulations')
    parser.add_argument('--program', type=str, default='Nurse', choices=['University', 'Nurse', 'Trade'],
                        help='Program type (Uganda, Kenya, or Rwanda)')
    parser.add_argument('--scenario', type=str, default='baseline', 
                        choices=['baseline', 'conservative', 'optimistic', 'custom'],
                        help='Scenario to run')
    parser.add_argument('--sims', type=int, default=1, help='Number of simulations')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--investment', type=float, default=1000000, help='Initial investment amount')
    parser.add_argument('--years', type=int, default=55, help='Number of years to simulate')
    parser.add_argument('--remittance-rate', type=float, default=0.1, help='Remittance rate')
    parser.add_argument('--home-prob', type=float, default=0.84, help='Probability of returning home (GiveWell baseline: 84%, meaning 16% stay earning non-counterfactual income)')
    
    args = parser.parse_args()
    
    # Get price per student based on program type
    if args.program == 'University':
        price_per_student = 30012  # GiveWell analysis cost per student
        program_display_name = 'Uganda'
    elif args.program == 'Nurse':
        price_per_student = 16650
        program_display_name = 'Kenya'
    elif args.program == 'Trade':
        price_per_student = 16650
        program_display_name = 'Rwanda'
    else:
        raise ValueError("Program type must be 'University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda)")
    
    # Calculate initial number of students that can be funded
    # Reserve 2% of investment for cash buffer
    available_for_students = args.investment * 0.98
    initial_students = int(available_for_students / price_per_student)
    
    print(f"\nRunning {args.scenario} scenario for {program_display_name} program")
    print(f"Initial investment: ${args.investment:,.2f}")
    print(f"Price per student: ${price_per_student:,.2f}")
    print(f"Initial students that can be funded: {initial_students}")
    
    # Set random seed if provided
    if args.seed is not None:
        np.random.seed(args.seed)
    
    # Set up impact parameters
    # Counterfactual household model:
    # - 5 members in counterfactual household (including control)
    # - 2 earners, each earning $1,503/year
    # - Per-person consumption = (2 * $1,503) / 5 = $601.20
    # Remittance receiving household:
    # - 4 members (treated is in Germany)
    # - 2 earners, each earning $1,503/year
    
    impact_params = ImpactParams(
        discount_rate=0.04,
        counterfactual=CounterfactualParams(
            base_earnings=1503,  # Base earnings per earner ($1,503/year) - matches spouse income in GiveWell
            earnings_growth=0.01,
            remittance_rate=0.0,
            employment_rate=1.0,  # No longer used - counterfactual assumes full employment
            household_size_counterfactual=5,  # HH size including control (GiveWell: 5)
            household_size_remittance=4,  # HH size for remittance recipients (treated in Germany)
            num_earners=2,  # Number of earners in household
            control_earner_multiplier=1.0  # Control earner earns same as other earner
        ),
        ppp_multiplier=0.42,
        health_benefit_per_euro=0.00003,
        migration_influence_factor=0.05,
        moral_weight=1.44
    )
    
    # Run simulation
    results = run_impact_simulation(
        program_type=args.program,
        initial_investment=args.investment,
        num_years=args.years,
        impact_params=impact_params,
        num_sims=args.sims,
        scenario=args.scenario,
        remittance_rate=args.remittance_rate,
        home_prob=args.home_prob
    )
    
    # Print standard summary
    print("\nPortfolio Performance Summary")
    print("=" * 40)
    print(f"Initial Investment: ${results['initial_investment']:,.2f}")
    print(f"Price per Student: ${results['price_per_student']:,.2f}")
    print(f"Initial Students Funded: {initial_students}")
    print(f"\nISA Parameters:")
    print(f"  - Percentage: {results['isa_percentage']*100:.1f}%")
    print(f"  - Cap: ${results['isa_cap']:,.2f}")
    print(f"  - Threshold: €{results['isa_threshold']:,.2f}")
    
    print("\nFinancial Metrics:")
    print(f"Average Total Payments: ${results['financial_metrics']['avg_total_payments']:,.2f}")
    print(f"Average Total Students Funded: {results['financial_metrics']['avg_students_funded']:.1f}")
    print(f"Average Students per Initial Investment: {results['financial_metrics']['avg_students_funded']/initial_students:.2f}x")
    
    print("\nImpact Metrics:")
    print(f"Average Utility Gain: {results['impact_metrics']['avg_utility_gain']:.2f}")
    print(f"Average Earnings Gain: €{results['impact_metrics']['avg_earnings_gain']:,.2f}")
    print(f"Average Remittance Gain: €{results['impact_metrics']['avg_remittance_gain']:,.2f}")
    
    # Print student outcomes if available
    if results.get('student_outcomes'):
        print("\nStudent Outcomes:")
        for metric, value in results['student_outcomes'].items():
            print(f"{metric.replace('_', ' ').title()}: {value:.2f}")

if __name__ == "__main__":
    main() 
