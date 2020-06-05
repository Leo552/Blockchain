# Made by Leo

import random
import math

class RSA_encrypt:
    def __init__(self):
        # p - large prime
        # q - large prime
        # n = p * q
        # phi = phi(n) = phi(p) * phi(q) = (p-1)(q-1)
        # e - integer coprime to phi
        # d - multiplicative inverse of with respect to e and phi
        
        e,d,n = self.generate_keys()
        
        self.pk_e = e
        self.pk_n = n
        self.__sk_d = d
    #    print(e,d,n)
    
    def decrypt_(self, cipher_text):
        d = self.__sk_d 
        n = self.pk_n
        plaintext = [chr((char ** d) % n) for char in cipher_text]
        
        return ''.join(plaintext)
    
    def decrypt(self, cipher_text, d, n):
        plaintext = [chr((char ** d) % n) for char in cipher_text]
        
        return ''.join(plaintext)
    
    def encrypt(self, plaintext, e, n):
        cipher_text = [(ord(char) ** e) % n for char in plaintext]
        
        return cipher_text
    
    def sign(self, text):
        return self.encrypt(text, self.__sk_d, self.pk_n)
    
    def verify(self, signature, e, n):
        return self.decrypt(signature, e, n)
        
    def generate_keys(self):

        # Generate two large primes for p and q
        p = self.gen_primes()
        q = self.gen_primes()
        
        # n is the product of the primes
        n = p * q
        
        # Phi is the totient of n
        phi = (p - 1) * (q - 1)
        
        # e is an integer such that is coprime to n
        e = random.randint(1, 100)
        
        # Use Euclid algorithm to make sure that e and phi are coprime
        g = self.gcd(e, phi)
        while g != 1:
             e = random.randint(1, 100)
             g = self.gcd(e, phi)           
        
        # Use the extended Euclidian algorithm to generate the private key
        d = self.modInverse(e, phi)
        
        # Return the public and private key pairs
        return e, d, n
    
    def modInverse(self, a, m) : 
        m0 = m 
        y = 0
        x = 1
      
        if (m == 1) : 
            return 0
      
        while (a > 1) : 
      
            # q is quotient 
            q = a // m 
      
            t = m 
      
            # m is remainder now, process 
            # same as Euclid's algo 
            m = a % m 
            a = t 
            t = y 
      
            # Update x and y 
            y = x - q * y 
            x = t 
      
      
        # Make x positive 
        if (x < 0) : 
            x = x + m0 
      
        return x 
      
    def gcd(self, a, b):
        while b != 0:
            a, b = b, a % b
        return a
    
    def gen_primes(self):
        while True:
            num = random.randint(100, 1000)
            if self.is_prime(num):
                return num
    
    def is_prime(self, n):
        if n <= 3:
            return n > 1
        elif n % 2 == 0 or n % 3 == 0:
            return False
        
        for i in range(5, math.floor(math.sqrt(n)), 6):
            if n % i == 0 or n % (i + 2) == 0:
                return False
        
        return True

if __name__ == '__main__':
    RSA = RSA_encrypt()
    c = RSA.encrypt('Helloooo', RSA.pk_e, RSA.pk_n)
    print(c)
    print(RSA.decrypt_(c))