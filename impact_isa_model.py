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
    base_earnings: float  # Base annual earnings without education
    earnings_growth: float  # Annual growth rate of earnings
    remittance_rate: float  # Percentage of income sent as remittances
    employment_rate: float  # Baseline employment rate

@dataclass
class ImpactParams:
    """Parameters for measuring social impact"""
    discount_rate: float  # Annual discount rate for utility calculations
    counterfactual: CounterfactualParams
    ppp_multiplier: float = 0.42  # Purchasing power parity multiplier for German to Ugandan earnings
    health_benefit_per_dollar: float = 0.00003  # Health utility gained per dollar of additional income (based on GiveWell's approach)
    migration_influence_factor: float = 0.05  # Additional people who migrate due to observing success
    moral_weight: float = 1.44  # Moral weight (alpha) for direct income effects, based on GiveWell's approach

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
                 starting_age: int = 22, retirement_age: int = 65):
        """Initialize a student with the given degree parameters."""
        self.degree = degree
        self.num_years = num_years
        self.counterfactual_params = counterfactual_params
        
        # Age tracking
        self.starting_age = starting_age
        self.retirement_age = retirement_age
        self.current_age = starting_age
        
        # Career tracking
        self.years_experience = 0
        self.earnings_power = 0
        self.is_graduated = False
        self.is_employed = False
        self.is_home = False
        
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
        """Check if the student has graduated by the given year."""
        return relative_year >= self.degree.years_to_complete

    def calculate_earnings(self, relative_year: int, year: Year) -> float:
        """
        Calculate earnings for the given year, considering graduation status,
        employment, and career progression.
        """
        # Update current age
        self.current_age = self.starting_age + relative_year
        
        # Check if student has graduated
        self.is_graduated = self.has_graduated(relative_year)
        
        # If not graduated or past retirement, no earnings
        if not self.is_graduated or self.current_age >= self.retirement_age:
            return 0
            
        # Check if student has returned home - if so, they should not benefit from education
        # They should earn at counterfactual levels instead
        if self.will_return_home and relative_year >= self.degree.years_to_complete:
            self.is_home = True
            # Use counterfactual earnings for home returns
            return self.calculate_counterfactual_earnings(relative_year, year)
        
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
        if relative_year == self.degree.years_to_complete or self.earnings_power == 0:
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
        """Calculate what the student would have earned without the program."""
        # If past retirement age, no earnings
        if self.starting_age + relative_year >= self.retirement_age:
            return 0
        
        # Simple employment check with fixed rate
        is_employed = np.random.binomial(1, self.counterfactual_params.employment_rate) == 1
        if not is_employed:
            return 0
        
        # Fixed base value that grows with inflation
        return 2400 * year.deflator

    def calculate_utility(self, income: float, alpha: float) -> float:
        """Calculate utility for a given income level."""
        return calculate_utility(income)

    def calculate_statistics(self, year: Year) -> Dict:
        """Calculate various statistics for the student's outcomes."""
        # Calculate total earnings and counterfactual earnings in real terms
        total_earnings = np.sum(self.earnings / year.deflator)
        total_counterfactual = np.sum(self.counterfactual_earnings / year.deflator)
        earnings_gain = total_earnings - total_counterfactual
        
        # Calculate remittances (15% of earnings) in real terms
        remittance_rate = 0.15
        remittances = self.earnings * remittance_rate / year.deflator
        counterfactual_remittances = self.counterfactual_earnings * remittance_rate / year.deflator
        remittance_gain = np.sum(remittances) - np.sum(counterfactual_remittances)
        
        # Calculate student utility using GiveWell's approach with moral weight of 1.44
        moral_weight = 1.44  # GiveWell's moral weight (alpha)
        student_utility = np.sum([
            moral_weight * calculate_utility(e/d - r/d)
            for e, r, d in zip(self.earnings, remittances, [year.deflator] * len(self.earnings))
        ])
        counterfactual_utility = np.sum([
            moral_weight * calculate_utility(e/d - r/d)
            for e, r, d in zip(self.counterfactual_earnings, counterfactual_remittances, [year.deflator] * len(self.counterfactual_earnings))
        ])
        utility_gain = student_utility - counterfactual_utility
        
        # Calculate remittance utility (4 family members)
        base_consumption = 511  # Updated to match GiveWell's BOTEC
        remittance_utility = np.sum([
            calculate_remittance_utility(r/d, base_consumption)
            for r, d in zip(remittances, [year.deflator] * len(remittances))
        ])
        counterfactual_remittance_utility = np.sum([
            calculate_remittance_utility(r/d, base_consumption)
            for r, d in zip(counterfactual_remittances, [year.deflator] * len(counterfactual_remittances))
        ])
        remittance_utility_gain = remittance_utility - counterfactual_remittance_utility
        
        # Calculate PPP-adjusted earnings gain (applying PPP multiplier to convert German earnings to Ugandan equivalent)
        ppp_adjusted_earnings_gain = earnings_gain * 0.42
        
        # Calculate health benefits using GiveWell's approach
        # Life expectancy improvement from 62 to 81 years (19 years)
        # Value of 40 units for this improvement, discounted at 5%
        # This results in approximately 3 utils per student, which is a fraction of income utility (about 160)
        health_utility = 3.0  # Fixed value based on GiveWell's approach
        
        # Calculate follow-the-leader migration effects
        migration_utility = 0
        if self.is_graduated and not self.is_home:
            # Each successful graduate influences 0.05 additional people to migrate
            # They get the same utility gain as this student
            migration_utility = (utility_gain + remittance_utility_gain) * 0.05
        
        return {
            'earnings_gain': earnings_gain,
            'ppp_adjusted_earnings_gain': ppp_adjusted_earnings_gain,
            'remittance_gain': remittance_gain,
            'utility_gains': {
                'student_utility_gain': utility_gain,
                'remittance_utility_gain': remittance_utility_gain,
                'total_utility_gain': utility_gain + remittance_utility_gain
            },
            'health_utility': health_utility,
            'migration_utility': migration_utility,
            'total_earnings': total_earnings,
            'total_counterfactual': total_counterfactual,
            'total_remittances': np.sum(remittances),
            'total_counterfactual_remittances': np.sum(counterfactual_remittances)
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
                    # If they're still in school or recently graduated, mark as home_return
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

def calculate_remittance_utility(remittance_amount: float, base_consumption: float = 511, num_recipients: int = 4) -> float:
    """
    Calculate utility gain from remittances for family members.
    Uses GiveWell's approach of comparing log utilities of consumption with and without remittances.
    
    Args:
        remittance_amount: Annual remittance amount
        base_consumption: Base annual consumption per family member ($511 from GiveWell BOTEC)
        num_recipients: Number of family members receiving remittances
        
    Returns:
        Total utility gain from remittances across all recipients
    """
    if remittance_amount <= 0:
        return 0
        
    # Each recipient gets an equal share
    remittance_per_person = remittance_amount / num_recipients
    
    # Calculate utility gain per person: ln(base + remittance) - ln(base)
    # First year value per person is about 5.1 utils according to GiveWell
    utility_gain_per_person = np.log(base_consumption + remittance_per_person) - np.log(base_consumption)
    
    # Apply household multiplier of 1.2 from GiveWell BOTEC
    household_multiplier = 1.2
    
    # Total utility gain across all recipients with household multiplier
    # According to GiveWell, this should be about 6.4 utils in the first year
    # And about 63-101 utils when properly discounted over lifetime
    return utility_gain_per_person * num_recipients * household_multiplier

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

def calculate_total_utility(earnings: float, counterfactual: float, remittance_rate: float, moral_weight: float = 1.44) -> Dict[str, float]:
    """
    Calculate total utility including both student and remittance impacts.
    
    Args:
        earnings: Total earnings
        counterfactual: Counterfactual earnings
        remittance_rate: Percentage of earnings sent as remittances
        moral_weight: Moral weight (alpha) for direct income effects
        
    Returns:
        Dictionary containing student utility, remittance utility, and total utility
    """
    remittance = earnings * remittance_rate
    
    student_utility = calculate_student_utility(earnings, counterfactual, remittance, moral_weight)
    remittance_utility = calculate_remittance_utility(remittance)
    
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
    - num_years: Number of years in simulation
    - remittance_rate: Percentage of income sent as remittances
    - impact_params: Parameters for impact calculation
    
    Returns:
    - Dictionary of student statistics
    """
    # Calculate lifetime earnings
    lifetime_earnings = np.sum(student.earnings)
    
    # Calculate real (present value) earnings
    discount_factors = np.array([(1 / (1 + impact_params.discount_rate)) ** t for t in range(num_years)])
    lifetime_real_earnings = np.sum(student.earnings[:len(discount_factors)] * discount_factors[:len(student.earnings)])
    
    # Calculate counterfactual lifetime earnings
    counterfactual_lifetime_earnings = np.sum(student.counterfactual_earnings)
    
    # Calculate remittances
    lifetime_remittances = lifetime_earnings * remittance_rate
    counterfactual_remittances = counterfactual_lifetime_earnings * impact_params.counterfactual.remittance_rate
    
    # Calculate yearly utilities with proper discounting
    yearly_utilities = []
    yearly_counterfactual_utilities = []
    
    for year in range(len(student.earnings)):
        if year < len(student.earnings):
            # Apply discount factor for this year
            discount_factor = (1 / (1 + impact_params.discount_rate)) ** year if year < len(discount_factors) else 0
            
            # Calculate utilities for this year
            year_utils = calculate_total_utility(
                student.earnings[year],
                student.counterfactual_earnings[year],
                remittance_rate,
                impact_params.moral_weight
            )
            
            # Apply discount factor to all utility components
            for key in year_utils:
                year_utils[key] *= discount_factor
                
            yearly_utilities.append(year_utils)
            
            # Counterfactual utilities (only remittances from base earnings)
            counterfactual_utils = calculate_total_utility(
                student.counterfactual_earnings[year],
                0,  # No counterfactual to counterfactual
                impact_params.counterfactual.remittance_rate,
                impact_params.moral_weight
            )
            
            # Apply discount factor to counterfactual utilities
            for key in counterfactual_utils:
                counterfactual_utils[key] *= discount_factor
                
            yearly_counterfactual_utilities.append(counterfactual_utils)
    
    # Sum utilities over time
    total_student_utility = sum(u['student_utility'] for u in yearly_utilities)
    total_remittance_utility = sum(u['remittance_utility'] for u in yearly_utilities)
    total_utility = sum(u['total_utility'] for u in yearly_utilities)
    
    counterfactual_student_utility = sum(u['student_utility'] for u in yearly_counterfactual_utilities)
    counterfactual_remittance_utility = sum(u['remittance_utility'] for u in yearly_counterfactual_utilities)
    counterfactual_total_utility = sum(u['total_utility'] for u in yearly_counterfactual_utilities)
    
    # Calculate utility gains
    utility_gains = {
        'student_utility_gain': total_student_utility - counterfactual_student_utility,
        'remittance_utility_gain': total_remittance_utility - counterfactual_remittance_utility,
        'total_utility_gain': total_utility - counterfactual_total_utility
    }
    
    # Calculate employment statistics
    years_employed = np.sum(student.employment_history)
    
    # Calculate ISA payments
    total_isa_payments = np.sum(student.payments)
    
    # Calculate PPP-adjusted earnings gain
    ppp_adjusted_earnings_gain = (lifetime_earnings - counterfactual_lifetime_earnings) * impact_params.ppp_multiplier
    
    # Calculate health benefits using GiveWell's approach
    # Life expectancy improvement from 62 to 81 years (19 years)
    # Value of 40 units for this improvement, discounted at 5%
    # This results in approximately 3 utils per student, which is a fraction of income utility (about 160)
    health_utility = 3.0  # Fixed value based on GiveWell's approach
    
    # Calculate follow-the-leader migration effects
    migration_utility = 0
    if student.is_graduated and not student.is_home:
        # Calculate average utility gain for a successful migrant
        avg_utility_gain = utility_gains['total_utility_gain']
        # Each graduate influences impact_params.migration_influence_factor additional people
        migration_utility = avg_utility_gain * impact_params.migration_influence_factor
    
    # Update total utility gains with new factors
    utility_gains['health_utility_gain'] = health_utility
    utility_gains['migration_influence_utility_gain'] = migration_utility
    utility_gains['total_utility_gain_with_extras'] = (
        utility_gains['total_utility_gain'] + 
        health_utility + 
        migration_utility
    )
    
    return {
        'degree_type': student.degree.name,
        'graduated': student.is_graduated,
        'dropped_out': not student.is_graduated,
        'lifetime_earnings': lifetime_earnings,
        'lifetime_real_earnings': lifetime_real_earnings,
        'counterfactual_lifetime_earnings': counterfactual_lifetime_earnings,
        'earnings_gain': lifetime_earnings - counterfactual_lifetime_earnings,
        'ppp_adjusted_earnings_gain': ppp_adjusted_earnings_gain,
        'lifetime_remittances': lifetime_remittances,
        'counterfactual_remittances': counterfactual_remittances,
        'remittance_gain': lifetime_remittances - counterfactual_remittances,
        'utility_gains': utility_gains,
        'health_utility': health_utility,
        'migration_utility': migration_utility,
        'years_employed': years_employed,
        'total_isa_payments': total_isa_payments,
        'years_paid_isa': student.years_paid,
        'hit_payment_cap': student.hit_cap,
        'yearly_utilities': yearly_utilities,
        'yearly_counterfactual_utilities': yearly_counterfactual_utilities
    }

def simulate_impact(
    program_type: str,
    initial_investment: float,
    num_years: int,
    impact_params: ImpactParams,
    num_sims: int = 1,
    scenario: str = 'baseline',
    remittance_rate: float = 0.15,
    home_prob: float = 0.1,
    data_callback: Optional[Callable] = None,
    isa_percentage: Optional[float] = None,
    isa_cap: Optional[float] = None,
    isa_threshold: Optional[float] = None,
    price_per_student: Optional[float] = None,
    initial_inflation_rate: float = 0.02,
    initial_unemployment_rate: float = 0.1,
    degree_params: Optional[List[tuple]] = None
) -> Dict:
    """
    Run a simulation of the impact of an ISA program.
    
    Parameters:
    - program_type: Type of program ('University', 'Nurse', or 'Trade')
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
    
    Returns:
    - Dictionary of simulation results
    """
    # Set default ISA parameters based on program type if not provided
    if isa_percentage is None:
        if program_type == 'University':
            isa_percentage = 0.14
        elif program_type == 'Nurse':
            isa_percentage = 0.12
        elif program_type == 'Trade':
            isa_percentage = 0.12
        else:
            isa_percentage = 0.12
    
    if isa_cap is None:
        if program_type == 'University':
            isa_cap = 72500
        elif program_type == 'Nurse':
            isa_cap = 49950
        elif program_type == 'Trade':
            isa_cap = 45000
        else:
            isa_cap = 50000
    
    if isa_threshold is None:
        isa_threshold = 27000
    
    if price_per_student is None:
        if program_type == 'University':
            price_per_student = 29000
        elif program_type == 'Nurse':
            price_per_student = 16650
        elif program_type == 'Trade':
            price_per_student = 15000
        else:
            raise ValueError("Program type must be 'University', 'Nurse', or 'Trade'")
    
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
        student = Student(degree_type, num_years, impact_params.counterfactual)
        student.id = i
        students.append(student)
        pool.add_student(student)  # Add student to pool
        # Use initial price (no inflation adjustment needed for year 0)
        pool.invest(price_per_student, 0, num_years)
    
    # Track yearly data
    yearly_data = []
    
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
            
            # Check for home return
            if student.is_graduated and student.will_return_home and relative_year >= student.degree.years_to_complete:
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
                student = Student(degree_type, num_years - i, impact_params.counterfactual)
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
                stats = student.calculate_statistics(year)
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
        'total_payments': total_payments
    }

def run_impact_simulation(
    program_type: str,
    initial_investment: float,
    num_years: int,
    impact_params: ImpactParams,
    num_sims: int = 1,
    scenario: str = 'baseline',
    remittance_rate: float = 0.15,
    home_prob: float = 0.1,
    data_callback: Optional[Callable] = None,
    isa_percentage: Optional[float] = None,
    isa_cap: Optional[float] = None,
    isa_threshold: Optional[float] = None,
    price_per_student: Optional[float] = None,
    initial_inflation_rate: float = 0.02,
    initial_unemployment_rate: float = 0.1,
    degree_params: Optional[List[tuple]] = None
) -> Dict:
    """
    Run multiple simulations of the ISA program and aggregate results.
    
    Args:
        program_type (str): Type of program ('University', 'Nurse', or 'Trade')
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
        
    Returns:
        dict: Aggregated simulation results
    """
    # Set defaults based on program type
    if isa_percentage is None:
        if program_type == 'University':
            isa_percentage = 0.14
        elif program_type == 'Nurse':
            isa_percentage = 0.12
        elif program_type == 'Trade':
            isa_percentage = 0.12
        else:
            isa_percentage = 0.12
    
    if isa_cap is None:
        if program_type == 'University':
            isa_cap = 72500
        elif program_type == 'Nurse':
            isa_cap = 49950
        elif program_type == 'Trade':
            isa_cap = 45000
        else:
            isa_cap = 50000
    
    if price_per_student is None:
        if program_type == 'University':
            price_per_student = 29000
        elif program_type == 'Nurse':
            price_per_student = 16650
        elif program_type == 'Trade':
            price_per_student = 15000
        else:
            raise ValueError("Program type must be 'University', 'Nurse', or 'Trade'")
        
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
            degree_params=degree_params
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
    
    if program_type == 'University':
        # For University programs
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
            ), 0.3)   # 30% MA
        ]
    elif program_type == 'Nurse':
        # For Nurse programs
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
            ), 0.60),  # 60% ASST
            (DegreeParams(
                name='NA',
                initial_salary=2200,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0  # Fixed high home probability for NA
            ), 0.15)   # 15% NA
        ]
    elif program_type == 'Trade':
        # For Trade programs
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
            ), 0.40),  # 40% ASST
            (DegreeParams(
                name='NA',
                initial_salary=2200,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0  # Fixed high home probability for NA
            ), 0.20)   # 20% NA
        ]
    else:
        raise ValueError("Program type must be 'University', 'Nurse', or 'Trade'")

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

def main():
    """
    Main function to demonstrate the usage of the ISA impact model.
    
    This function runs several example simulations and prints the results.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run ISA impact simulations')
    parser.add_argument('--program', type=str, default='Nurse', choices=['University', 'Nurse', 'Trade'],
                        help='Program type (University, Nurse, or Trade)')
    parser.add_argument('--scenario', type=str, default='baseline', 
                        choices=['baseline', 'conservative', 'optimistic', 'custom'],
                        help='Scenario to run')
    parser.add_argument('--sims', type=int, default=1, help='Number of simulations')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility')
    parser.add_argument('--investment', type=float, default=1000000, help='Initial investment amount')
    parser.add_argument('--years', type=int, default=55, help='Number of years to simulate')
    parser.add_argument('--remittance-rate', type=float, default=0.1, help='Remittance rate')
    parser.add_argument('--home-prob', type=float, default=0.1, help='Probability of returning home')
    
    args = parser.parse_args()
    
    # Get price per student based on program type
    if args.program == 'University':
        price_per_student = 29000
    elif args.program == 'Nurse':
        price_per_student = 16650
    elif args.program == 'Trade':
        price_per_student = 15000
    else:
        raise ValueError("Program type must be 'University', 'Nurse', or 'Trade'")
    
    # Calculate initial number of students that can be funded
    # Reserve 2% of investment for cash buffer
    available_for_students = args.investment * 0.98
    initial_students = int(available_for_students / price_per_student)
    
    print(f"\nRunning {args.scenario} scenario for {args.program} program")
    print(f"Initial investment: ${args.investment:,.2f}")
    print(f"Price per student: ${price_per_student:,.2f}")
    print(f"Initial students that can be funded: {initial_students}")
    
    # Set random seed if provided
    if args.seed is not None:
        np.random.seed(args.seed)
    
    # Set up impact parameters
    impact_params = ImpactParams(
        discount_rate=0.05,
        counterfactual=CounterfactualParams(
            base_earnings=2200,
            earnings_growth=0.01,
            remittance_rate=0.15,
            employment_rate=0.9
        ),
        ppp_multiplier=0.42,
        health_benefit_per_dollar=0.00003,
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
    print(f"  - Threshold: ${results['isa_threshold']:,.2f}")
    
    print("\nFinancial Metrics:")
    print(f"Average Total Payments: ${results['financial_metrics']['avg_total_payments']:,.2f}")
    print(f"Average Total Students Funded: {results['financial_metrics']['avg_students_funded']:.1f}")
    print(f"Average Students per Initial Investment: {results['financial_metrics']['avg_students_funded']/initial_students:.2f}x")
    
    print("\nImpact Metrics:")
    print(f"Average Utility Gain: {results['impact_metrics']['avg_utility_gain']:.2f}")
    print(f"Average Earnings Gain: ${results['impact_metrics']['avg_earnings_gain']:,.2f}")
    print(f"Average Remittance Gain: ${results['impact_metrics']['avg_remittance_gain']:,.2f}")
    
    # Print student outcomes if available
    if results.get('student_outcomes'):
        print("\nStudent Outcomes:")
        for metric, value in results['student_outcomes'].items():
            print(f"{metric.replace('_', ' ').title()}: {value:.2f}")

if __name__ == "__main__":
    main() 