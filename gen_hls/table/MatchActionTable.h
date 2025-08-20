#ifndef MATCH_ACTION_TABLE_H
#define MATCH_ACTION_TABLE_H

#include "../common/Shared.h"
#include "../header/Header.h"
#include "../ingress/MemoryInterface.h"

// TS: Table Depth Size, MS: Match-key Size, AS: Action Size
template<int TS, int MS, int AS, MatchActionTableType TABLE_TYPE>
class MatchActionTable {
public:
	MatchActionTable() {}
    ~MatchActionTable() {}

	int jenkins_hash(const ap_uint<MS> &key) const {
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		unsigned int hash = 0;
		constexpr int bytesize = (MS + 7) / 8;
		L_HASH: for (int i = 0; i < bytesize; i++) {
#pragma HLS UNROLL
#pragma HLS LOOP_TRIPCOUNT max=8
//#pragma HLS PIPELINE II=1
			hash += (i == bytesize -1) ? key.range(MS-1, i*8).to_uint() : key.range(i*8+7, i*8).to_uint();
			hash += (hash << 10);
			hash ^= (hash >> 6);
		}
		hash += (hash << 3);
		hash ^= (hash >> 11);
		hash += (hash << 15);
		return hash;
	}

	int FNV1a_hash(const ap_uint<MS> &key) const {
#pragma HLS PIPELINE II=1
		constexpr int bytesize = (MS + 7) / 8;
		const ap_uint<bytesize*8> data(key);
		unsigned int hash[bytesize+1];
		hash[0] = 2166136261u; // 0x 811C 9DC5

		for (int i = 0; i < bytesize; i++) {
//#pragma HLS PIPELINE II=1
#pragma HLS UNROLL
			hash[i+1] = (hash[i] ^ data.range(i*8+7, i*8)) * 16777619u;
		}

		return hash[bytesize];
	}

	int hash_function(const ap_uint<MS> &key) const {
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
//		return jenkins_hash(key) % TS;
		return FNV1a_hash(key) % TS;
	}

    // Insert an entry
	void insert_entry(unsigned int *memPtr, const ap_uint<MS> &key, const ap_uint<AS> &value) {
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		int index = hash_function(key);
		// TODO: Check if any hash collision occurs
#if defined(DDR) or defined(HBM)
		MemoryInterface::getInstance().update_entry<TS, MS, AS, TABLE_TYPE>(memPtr, index, LookupEntry<MS, AS>(key, value, true));
#elif defined(BRAM) or defined(URAM)
		MemoryInterface::getInstance().update_entry<TS, MS, AS, TABLE_TYPE>(lookup, index, LookupEntry<MS, AS>(key, value, true));
#endif
    }

    // Delete an entry
	bool delete_entry(unsigned int *memPtr, const ap_uint<MS> &key, const ap_uint<AS> &value) {
#pragma HLS INLINE
		int index = hash_function(key);
#if defined(DDR) or defined(HBM)		
		return MemoryInterface::getInstance().delete_entry<TS, MS, AS, TABLE_TYPE>(memPtr, index, key, value);
#elif defined(BRAM) or defined(URAM)	
        return MemoryInterface::getInstance().delete_entry<TS, MS, AS, TABLE_TYPE>(lookup, index, key, value);	
#endif	
	}

    // Search an index
	bool search_index(const unsigned int *memPtr, const ap_uint<MS> &key, int &index) {
#pragma HLS INLINE
		index = hash_function(key);
#if defined(DDR) or defined(HBM)
		return MemoryInterface::getInstance().search_index<TS, MS, AS, TABLE_TYPE>(memPtr, index, key);
#elif defined(BRAM) or defined(URAM)
		return MemoryInterface::getInstance().search_index<TS, MS, AS, TABLE_TYPE>(lookup, index, key);
#endif
    }

    // Search an entry
	bool search_entry(const unsigned int *memPtr, const ap_uint<MS> &key, ap_uint<AS> &value) {
#pragma HLS INLINE
//#pragma HLS PIPELINE II=1
		int index = hash_function(key);
#if defined(DDR) or defined(HBM)		
		return MemoryInterface::getInstance().search_entry<TS, MS, AS, TABLE_TYPE>(memPtr, index, key, value);
#elif defined(BRAM) or defined(URAM)
		return MemoryInterface::getInstance().search_entry<TS, MS, AS, TABLE_TYPE>(lookup, index, key, value);
#endif
    }

#if defined(BRAM) or defined(URAM)
	volatile LookupEntry<MS, AS> lookup[TS];
#endif
};

#endif // MATCH_ACTION_TABLE_H

