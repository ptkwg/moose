//* This file is part of the MOOSE framework
//* https://www.mooseframework.org
//*
//* All rights reserved, see COPYRIGHT for full restrictions
//* https://github.com/idaholab/moose/blob/master/COPYRIGHT
//*
//* Licensed under LGPL 2.1, please see LICENSE for details
//* https://www.gnu.org/licenses/lgpl-2.1.html

#include "OutputTestMaterial.h"

registerMooseObject("MooseTestApp", OutputTestMaterial);

template <>
InputParameters
validParams<OutputTestMaterial>()
{
  InputParameters params = validParams<Material>();
  params.addParam<std::string>(
      "real_property_name", "real_property", "The name of the scalar real property");
  params.addParam<std::string>(
      "vector_property_name", "vector_property", "The name of the vector real property");
  params.addParam<std::string>(
      "tensor_property_name", "tensor_property", "The name of the tensor real property");
  params.addParam<Real>(
      "real_factor", 0, "Add this factor to all of the scalar real material property");
  params.addCoupledVar("variable",
                       "Variable to use for making this test material more complicated");
  return params;
}

OutputTestMaterial::OutputTestMaterial(const InputParameters & parameters)
  : Material(parameters),
    _real_property(declareProperty<Real>(getParam<std::string>("real_property_name"))),
    _vector_property(
        declareProperty<RealVectorValue>(getParam<std::string>("vector_property_name"))),
    _tensor_property(
        declareProperty<RealTensorValue>(getParam<std::string>("tensor_property_name"))),
    _factor(getParam<Real>("real_factor")),
    _variable(coupledValue("variable"))
{
}

OutputTestMaterial::~OutputTestMaterial() {}

void
OutputTestMaterial::computeQpProperties()
{
  Point p = _q_point[_qp];
  Real v = std::floor(_variable[_qp] + 0.5);
  Real x = std::ceil(p(0));
  Real y = std::ceil(p(1));

  _real_property[_qp] = v + y + x + _factor;

  RealVectorValue vec(v + x, v + y);
  _vector_property[_qp] = vec;

  RealTensorValue tensor(v, x * y, 0, -x * y, y * y);
  _tensor_property[_qp] = tensor;
}
