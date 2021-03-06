//* This file is part of the MOOSE framework
//* https://www.mooseframework.org
//*
//* All rights reserved, see COPYRIGHT for full restrictions
//* https://github.com/idaholab/moose/blob/master/COPYRIGHT
//*
//* Licensed under LGPL 2.1, please see LICENSE for details
//* https://www.gnu.org/licenses/lgpl-2.1.html

#include "SinglePhaseFluidProperties.h"

template <>
InputParameters
validParams<SinglePhaseFluidProperties>()
{
  InputParameters params = validParams<FluidProperties>();

  return params;
}

SinglePhaseFluidProperties::SinglePhaseFluidProperties(const InputParameters & parameters)
  : FluidProperties(parameters)
{
}

SinglePhaseFluidProperties::~SinglePhaseFluidProperties() {}

Real
SinglePhaseFluidProperties::gamma_from_v_e(Real v, Real e) const
{
  return cp_from_v_e(v, e) / cv_from_v_e(v, e);
}
