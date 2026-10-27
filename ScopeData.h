#ifndef SCOPE_DATA_H
#define SCOPE_DATA_H

#include <stdint.h>

struct ScopeData {
  uint32_t t_us;
  float target;
  float angle;
  float uq;
  uint32_t enabled;
  uint32_t status;
  uint32_t n_fault;
  float ia;
  float ib;
  float ic;
  float va;
  float vb;
  float vc;
};

#endif
