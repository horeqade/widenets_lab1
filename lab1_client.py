import socket
from math import floor, log2, ceil

import numpy as np
from bitarray import bitarray

from wide_nets.lab1_server import _is_power_of_two, _powers_of_two, _calculate_parity


def _next_power_of_two(n: int):
    if (not (type(n) == int)) or (n <= 0):
        raise ValueError("Argument must be a positive integer.")
    elif _is_power_of_two(n):
        return n << 1
    return 2 ** ceil(log2(n))


def _num_parity_bits_needed(length: int):
    n = _next_power_of_two(length)
    lower_bin = floor(log2(n))
    upper_bin = lower_bin + 1
    data_bit_boundary = n - lower_bin - 1
    return lower_bin if length <= data_bit_boundary else upper_bin


def load_message():
    with open('message.txt', 'r', encoding='utf-8') as file:
        data = file.read().replace('\n', '')
    return data


def encode(txt: str):
    ba = bitarray()
    ba.frombytes(txt.encode('utf-8'))
    return ba


def decode(txt: bitarray):
    return txt.tobytes().decode('utf-8', 'ignore')


def byte2bit(b: bytes):
    ba = bitarray()
    ba.frombytes(b)
    return ba


def bit2byte(b: bitarray):
    return b.tobytes()


def noOfParityBits(noOfBits):
    i = 0
    while 2. ** i <= noOfBits + i:
        i += 1
    return i


def noOfParityBitsInCode(noOfBits):
    i = 0
    while 2. ** i <= noOfBits:
        i += 1

    return i


def appendParityBits(data):
    n = noOfParityBits(len(data))
    i = 0
    j = 0
    k = 0
    list1 = list()
    while i < n + len(data):
        if i == (2. ** j - 1):
            list1.insert(i, 0)
            j += 1
        else:
            list1.insert(i, data[k])
            k += 1
        i += 1
    return list1


def hammingCodes(data):
    n = noOfParityBits(len(data))
    list1 = appendParityBits(data)
    i = 0
    k = 1
    while i < n:
        k = 2. ** i
        j = 1
        total = 0
        while j * k - 1 < len(list1):
            if j * k - 1 == len(list1) - 1:
                lower_index = j * k - 1
                temp = list1[int(lower_index):len(list1)]
            elif (j + 1) * k - 1 >= len(list1):
                lower_index = j * k - 1
                temp = list1[int(lower_index):len(list1)]
            elif (j + 1) * k - 1 < len(list1) - 1:
                lower_index = (j * k) - 1
                upper_index = (j + 1) * k - 1
                temp = list1[int(lower_index):int(upper_index)]

            total = total + sum(int(e) for e in temp)
            j += 2
        if total % 2 > 0:
            list1[int(
                k) - 1] = 1
        i += 1
    return list1


def ham_encode(data: bitarray):
    data_length = len(data)
    num_parity_bits = _num_parity_bits_needed(data_length)
    encoded_length = data_length + num_parity_bits + 1

    encoded = bitarray(encoded_length)

    for parity_bit_index in _powers_of_two(num_parity_bits):
        encoded[parity_bit_index] = _calculate_parity(data, parity_bit_index)

    data_index = 0
    for encoded_index in range(3, len(encoded)):
        if not _is_power_of_two(encoded_index):
            encoded[encoded_index] = data[data_index]
            data_index += 1

    encoded[0] = _calculate_parity(encoded[1:], 0)
    return encoded


def inv_bit(arr, cnt):
    idx_arr = [3, 5, 10, 15]
    for i in range(cnt):
        idx = np.random.choice(len(arr))
        idx = idx_arr[i]
        arr[idx] = 1 - arr[idx]
    return arr


def text_hamming_bytes(text, mode=0, len_word=70):
    bits = encode(text)
    hamming = []
    cnt1err, cnt0err, cntMultiErr = 0, 0, 0
    for i in range(int(len(bits) / len_word) + 1):
        if i == int(len(bits) / len_word):
            hamming.append(ham_encode(bits[i * len_word:]))
        else:
            hamming.append(ham_encode(bits[i * len_word: (i + 1) * len_word]))
        if mode == 0:
            cnt0err += 1
        elif mode == 1:
            if i < (int(len(bits) / len_word) + 1) / 2:
                hamming[i] = inv_bit(hamming[i], 1)
                cnt1err += 1
            else:
                cnt0err += 1
        elif mode == 2:
            if i < (int(len(bits) / len_word) + 1) / 2:
                hamming[i] = inv_bit(hamming[i], 2)
                cntMultiErr += 1
            else:
                cnt0err += 1
        elif mode == 3:
            if i < (int(len(bits) / len_word) + 1) / 4:
                cnt0err += 1
            elif i < (int(len(bits) / len_word) + 1) / 2:
                hamming[i] = inv_bit(hamming[i], 1)
                cnt1err += 1
            elif i < 9 * (int(len(bits) / len_word) + 1) / 10:
                hamming[i] = inv_bit(hamming[i], 2)
                cntMultiErr += 1
            else:
                hamming[i] = inv_bit(hamming[i], 2)
                cntMultiErr += 1

    hamming = bitarray(bit for ham in hamming for bit in ham)
    return cnt0err, cnt1err, cntMultiErr, bit2byte(hamming)


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes(10, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')


def launch_client(mode=0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    msg = load_message()
    sock.connect(('localhost', 9090))
    cnt0err, cnt1err, cntMultiErr, code = text_hamming_bytes(msg, mode=mode)
    print(f"0 mistakes: {cnt0err}")
    print(f"1 mistakes: {cnt1err}")
    print(f"Multi mistakes: {cntMultiErr}")
    print()
    sock.send(code)
    print("Data sent")

    result_str = ""
    data = sock.recv(100000)
    sock.close()
    ints = data[:30]
    txt = data[30:]
    print(f"1 Error: {int_from_bytes(ints[:10])}")
    print(f"Correct words: {int_from_bytes(ints[10:20])}")
    print(f"Incorrect words: {int_from_bytes(ints[20:])}")
    print(decode(byte2bit(txt)))


if __name__ == '__main__':
    launch_client(mode=3)
    """bytes = int_to_bytes(2000) + int_to_bytes(10)
    print(bytes)
    print(int_from_bytes(bytes[10:]))"""

    """b = encode("University it is a cool")
    print(len(b))
    b = hammingCodes(b)
    print(len(b))
    b = hammingCorrection(b)
    print(len(b))
    print(decode(b))"""
